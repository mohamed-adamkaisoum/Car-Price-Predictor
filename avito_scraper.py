from __future__ import annotations

import argparse
import csv
import html
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode

import requests


BASE_URL = "https://www.avito.ma"
START_URL = f"{BASE_URL}/fr/maroc/voitures_d_occasion-%C3%A0_vendre"

FIELDNAMES = [
    "id",
    "list_id",
    "titre",
    "prix",
    "devise",
    "ville",
    "secteur",
    "localisation",
    "marque",
    "modele",
    "annee",
    "kilometrage",
    "carburant",
    "boite_vitesses",
    "puissance_fiscale",
    "etat",
    "origine",
    "premiere_main",
    "nombre_portes",
    "equipements",
    "vendeur",
    "type_vendeur",
    "telephone",
    "date_publication",
    "description",
    "image_url",
    "url",
]

PARAM_ALIASES = {
    "Marque": "marque",
    "Modèle": "modele",
    "Année-Modèle": "annee",
    "Kilométrage": "kilometrage",
    "Type de carburant": "carburant",
    "Boite de vitesses": "boite_vitesses",
    "Puissance fiscale": "puissance_fiscale",
    "État": "etat",
    "Origine": "origine",
    "Première main": "premiere_main",
    "Nombre de portes": "nombre_portes",
}

EQUIPMENT_LABELS = {
    "Jantes aluminium",
    "Airbags",
    "Climatisation",
    "Système de navigation/GPS",
    "Toit ouvrant",
    "Sièges cuir",
    "Radar de recul",
    "Caméra de recul",
    "Vitres électriques",
    "ABS",
    "ESP",
    "Régulateur de vitesse",
    "Limiteur de vitesse",
    "CD/MP3/Bluetooth",
    "Ordinateur de bord",
    "Verrouillage centralisé à distance",
}


class AvitoScraperError(RuntimeError):
    pass


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    return re.sub(r"\s+", " ", text).strip()


def extract_next_data(page_html: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        page_html,
        flags=re.DOTALL,
    )
    if not match:
        raise AvitoScraperError("Impossible de trouver le JSON __NEXT_DATA__ dans la page.")
    return json.loads(html.unescape(match.group(1)))


def get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def build_listing_url(page_number: int) -> str:
    if page_number <= 1:
        return START_URL
    return f"{START_URL}?{urlencode({'o': page_number})}"


def request_html(session: requests.Session, url: str, timeout: int = 30) -> str:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except (requests.RequestException, HTTPError) as exc:
            last_error = exc
            wait = attempt * 5
            print(f"[retry] {url} tentative {attempt}/3 apres erreur: {exc}", file=sys.stderr)
            time.sleep(wait)
    raise AvitoScraperError(f"Echec apres 3 tentatives: {url} ({last_error})")


def params_to_columns(params: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    row: dict[str, str] = {}
    equipments: list[str] = []

    for group in ("primary", "secondary", "extra"):
        for item in params.get(group, []) or []:
            label = clean_text(item.get("label") or item.get("name"))
            value = item.get("fullValue")
            if value is None:
                value = item.get("value")
            if value is None:
                value = item.get("textValue")
            if value is None:
                value = item.get("numericValue")
            value_text = clean_text(value)
            if not label or not value_text:
                continue

            column = PARAM_ALIASES.get(label)
            if column:
                row[column] = value_text
            elif label in EQUIPMENT_LABELS and value_text.lower() not in {"non", "false", "0"}:
                equipments.append(label)

    return row, equipments


def normalize_price(price: Any) -> tuple[str, str]:
    if not isinstance(price, dict) or not price:
        return "", ""
    value = price.get("value")
    currency = price.get("currency", "")
    if value is None:
        value = price.get("withoutCurrency")
    if value is None:
        with_currency = price.get("withCurrency")
        if with_currency:
            return clean_text(with_currency), clean_text(currency or "DH")
        return "", clean_text(currency)
    return clean_text(value), clean_text(currency or "DH")


def extract_image_url(data: Any) -> str:
    if isinstance(data, dict):
        for key in ("url", "href", "src", "large", "medium", "small"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return clean_text(value)
        for key in ("images", "pictures", "photos", "media"):
            value = data.get(key)
            image_url = extract_image_url(value)
            if image_url:
                return image_url
        for value in data.values():
            image_url = extract_image_url(value)
            if image_url:
                return image_url
    elif isinstance(data, list):
        for item in data:
            image_url = extract_image_url(item)
            if image_url:
                return image_url
    return ""


def row_from_listing_ad(ad: dict[str, Any]) -> dict[str, str]:
    price, currency = normalize_price(ad.get("price"))
    params, equipments = params_to_columns(ad.get("params") or {})
    seller = ad.get("seller") or {}

    row = {
        "id": clean_text(ad.get("id")),
        "list_id": clean_text(ad.get("listId")),
        "titre": clean_text(ad.get("subject")),
        "prix": price,
        "devise": currency,
        "localisation": clean_text(ad.get("location")),
        "vendeur": clean_text(seller.get("name")),
        "type_vendeur": clean_text(seller.get("type")),
        "telephone": clean_text(get_nested(seller, "phone", "number", default="")),
        "date_publication": clean_text(ad.get("date")),
        "description": clean_text(ad.get("description")),
        "image_url": extract_image_url(ad),
        "url": clean_text(ad.get("href")),
    }
    row.update(params)
    if equipments:
        row["equipements"] = ", ".join(sorted(set(equipments)))
    return ensure_fields(split_location(row))


def row_from_detail_ad(ad: dict[str, Any], fallback_url: str = "") -> dict[str, str]:
    price, currency = normalize_price(ad.get("price"))
    params, equipments = params_to_columns(ad.get("params") or {})
    seller = ad.get("seller") or {}
    location = ad.get("location") or {}
    city = get_nested(location, "city", "name", default="")
    area = get_nested(location, "area", "name", default="")
    full_location = ", ".join(part for part in [clean_text(city), clean_text(area)] if part)

    image_equipment = [
        item.get("label") or item.get("name")
        for item in (ad.get("params") or {}).get("extra", []) or []
        if clean_text(item.get("label") or item.get("name")) in EQUIPMENT_LABELS
    ]
    equipments.extend(clean_text(item) for item in image_equipment if item)

    row = {
        "id": clean_text(ad.get("id")),
        "list_id": clean_text(ad.get("listId")),
        "titre": clean_text(ad.get("subject")),
        "prix": price,
        "devise": currency,
        "ville": clean_text(city),
        "secteur": clean_text(area),
        "localisation": full_location,
        "vendeur": clean_text(seller.get("name")),
        "type_vendeur": clean_text(seller.get("type") or ad.get("sellerType")),
        "telephone": clean_text(ad.get("phone") or get_nested(seller, "phone", "number", default="")),
        "date_publication": clean_text(ad.get("listTime")),
        "description": clean_text(ad.get("description")),
        "image_url": extract_image_url(ad),
        "url": clean_text(get_nested(ad, "friendlyUrl", "url", default=fallback_url) or fallback_url),
    }
    row.update(params)
    if equipments:
        row["equipements"] = ", ".join(sorted(set(equipments)))
    return ensure_fields(row)


def split_location(row: dict[str, str]) -> dict[str, str]:
    location = row.get("localisation", "")
    if location and not row.get("ville"):
        parts = [part.strip() for part in location.split(",", 1)]
        row["ville"] = parts[0]
        if len(parts) > 1:
            row["secteur"] = parts[1]
    return row


def ensure_fields(row: dict[str, str]) -> dict[str, str]:
    return {field: clean_text(row.get(field, "")) for field in FIELDNAMES}


def extract_listing_ads(page_html: str) -> list[dict[str, Any]]:
    data = extract_next_data(page_html)
    ads = get_nested(data, "props", "pageProps", "componentProps", "ads", "ads")
    if not isinstance(ads, list):
        ads = get_nested(data, "props", "pageProps", "componentProps", "initialSearchResult", "ads")
    if not isinstance(ads, list):
        ads = get_nested(data, "props", "pageProps", "initialSearchResult", "ads")
    if not isinstance(ads, list):
        raise AvitoScraperError("Impossible de trouver les annonces dans le JSON de recherche.")
    return ads


def extract_detail_ad(page_html: str) -> dict[str, Any]:
    data = extract_next_data(page_html)
    ad = get_nested(data, "props", "pageProps", "apolloState", "ROOT_QUERY", "ad")
    if isinstance(ad, dict) and ad.get("subject"):
        return ad

    ad = get_nested(data, "props", "initialReduxState", "ad", "view", "adInfo")
    if isinstance(ad, dict) and ad.get("subject"):
        return ad

    ad = get_nested(data, "props", "pageProps", "initialReduxState", "ad", "view", "adInfo")
    if isinstance(ad, dict) and ad.get("subject"):
        return ad

    raise AvitoScraperError("Impossible de trouver les détails de l'annonce.")


def scrape(
    pages: int,
    output: Path,
    delay_min: float,
    delay_max: float,
    details: bool,
    limit: int | None,
    resume: bool,
    checkpoint_every: int,
) -> list[dict[str, str]]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
    )

    rows, seen_urls = load_existing_rows(output) if resume else ([], set())
    if rows:
        print(f"[resume] {len(rows)} annonces deja presentes dans {output}")

    for page_number in range(1, pages + 1):
        listing_url = build_listing_url(page_number)
        print(f"[page {page_number}] Lecture: {listing_url}")
        listing_html = request_html(session, listing_url)
        ads = extract_listing_ads(listing_html)
        print(f"[page {page_number}] {len(ads)} annonces trouvees")

        for ad in ads:
            if limit is not None and len(rows) >= limit:
                write_outputs(rows, output)
                return rows

            listing_row = row_from_listing_ad(ad)
            url = listing_row.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            if details:
                sleep_between(delay_min, delay_max)
                try:
                    detail_html = request_html(session, url)
                    detail_ad = extract_detail_ad(detail_html)
                    row = row_from_detail_ad(detail_ad, fallback_url=url)
                except Exception as exc:
                    print(f"[attention] Detail indisponible pour {url}: {exc}", file=sys.stderr)
                    row = listing_row
            else:
                row = listing_row

            rows.append(row)
            print(f"  + {len(rows):04d} {row['titre'][:70]}")
            if checkpoint_every and len(rows) % checkpoint_every == 0:
                write_outputs(rows, output)

        sleep_between(delay_min, delay_max)

    write_outputs(rows, output)
    return rows


def sleep_between(delay_min: float, delay_max: float) -> None:
    if delay_max <= 0:
        return
    time.sleep(random.uniform(max(0, delay_min), max(delay_min, delay_max)))


def write_outputs(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = write_csv_safely(rows, output)
    print(f"[ok] CSV ecrit: {csv_path}")

    xlsx_path = csv_path.with_suffix(".xlsx")
    try:
        import pandas as pd

        pd.DataFrame(rows, columns=FIELDNAMES).to_excel(xlsx_path, index=False)
        print(f"[ok] Excel ecrit: {xlsx_path}")
    except Exception as exc:
        print(f"[info] Excel non cree ({exc}). CSV disponible.", file=sys.stderr)


def write_csv_safely(rows: list[dict[str, str]], output: Path) -> Path:
    try:
        write_csv(rows, output)
        return output
    except PermissionError as exc:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback = output.with_name(f"{output.stem}_checkpoint_{timestamp}{output.suffix}")
        print(
            f"[warning] CSV principal verrouille ({exc}). Sauvegarde de secours: {fallback}",
            file=sys.stderr,
        )
        write_csv(rows, fallback)
        return fallback


def write_csv(rows: list[dict[str, str]], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def load_existing_rows(output: Path) -> tuple[list[dict[str, str]], set[str]]:
    if not output.exists():
        return [], set()

    with output.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = [ensure_fields(row) for row in reader]
    seen_urls = {row["url"] for row in rows if row.get("url")}
    return rows, seen_urls


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scraper Avito voitures d'occasion vers CSV/XLSX.")
    parser.add_argument("--pages", type=int, default=1, help="Nombre de pages de resultats a parcourir.")
    parser.add_argument("--limit", type=int, default=None, help="Nombre maximum d'annonces a extraire.")
    parser.add_argument("--output", type=Path, default=Path("data/avito_voitures.csv"), help="Chemin du CSV.")
    parser.add_argument("--delay-min", type=float, default=1.5, help="Pause minimum entre deux requetes.")
    parser.add_argument("--delay-max", type=float, default=3.5, help="Pause maximum entre deux requetes.")
    parser.add_argument("--checkpoint-every", type=int, default=100, help="Sauvegarde tous les N resultats.")
    parser.add_argument("--resume", action="store_true", help="Reprendre depuis le CSV existant sans doublons d'URL.")
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Ne pas ouvrir les pages detail. Plus rapide, mais moins complet.",
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    if args.pages < 1:
        raise SystemExit("--pages doit etre >= 1")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit doit etre >= 1")
    if args.delay_min > args.delay_max:
        raise SystemExit("--delay-min doit etre <= --delay-max")

    rows = scrape(
        pages=args.pages,
        output=args.output,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        details=not args.no_details,
        limit=args.limit,
        resume=args.resume,
        checkpoint_every=args.checkpoint_every,
    )
    print(f"[termine] {len(rows)} annonces sauvegardees")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
