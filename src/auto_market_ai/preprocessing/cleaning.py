from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import pandas as pd

from auto_market_ai.config import CURRENT_YEAR


PREMIUM_BRANDS = {
    "audi",
    "bmw",
    "mercedes-benz",
    "mercedes",
    "porsche",
    "land rover",
    "range rover",
    "jaguar",
    "lexus",
    "tesla",
    "volvo",
    "mini",
    "cupra",
    "bentley",
}

LUXURY_TERMS = {
    "amg",
    "m sport",
    "s-line",
    "s line",
    "r-line",
    "r line",
    "full option",
    "full options",
    "toit ouvrant",
    "cuir",
    "matrix",
    "pack",
    "exclusive",
    "autobiography",
    "maybach",
    "brabus",
    "carlex",
    "turbo",
    "v6",
    "v8",
    "hse",
    "fr",
    "gt",
    "gt line",
}

TRIM_PATTERNS = {
    "amg": r"\bamg\b",
    "s-line": r"\bs[\s-]?line\b",
    "r-line": r"\br[\s-]?line\b",
    "m-sport": r"\bm[\s-]?sport\b",
    "gt-line": r"\bgt[\s-]?line\b",
    "fr": r"\bfr\b",
    "exclusive": r"\bexclusive\b",
    "autobiography": r"\bautobiography\b",
    "hse": r"\bhse\b",
    "full-option": r"\bfull\s+options?\b",
}

EQUIPMENT_PATTERNS = {
    "equip_abs": ["abs"],
    "equip_airbags": ["airbag"],
    "equip_climatisation": ["climatisation", "clim"],
    "equip_gps": ["gps", "navigation"],
    "equip_toit_ouvrant": ["toit ouvrant", "toit panoramique", "panoramique"],
    "equip_cuir": ["cuir", "alcantara"],
    "equip_radar_recul": ["radar de recul", "radars"],
    "equip_camera_recul": ["camera de recul", "caméra de recul"],
    "equip_jantes": ["jantes", "jante aluminium"],
    "equip_bluetooth": ["bluetooth", "cd/mp3", "mp3"],
}

FUEL_MAP = {
    "diesel": "diesel",
    "essence": "essence",
    "hybride": "hybride",
    "electrique": "electrique",
    "électrique": "electrique",
    "lpg": "gpl",
    "gpl": "gpl",
}

TRANSMISSION_MAP = {
    "automatique": "automatique",
    "manuelle": "manuelle",
    "manual": "manuelle",
    "auto": "automatique",
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def strip_accents(value: object) -> str:
    text = normalize_text(value).lower()
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_category(value: object, mapping: dict[str, str] | None = None) -> str:
    text = normalize_text(value).lower()
    if not text:
        return "unknown"
    if mapping:
        for needle, replacement in mapping.items():
            if needle in text:
                return replacement
    return text


def parse_number(value: object) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    text = text.replace("\u202f", "").replace(",", "").replace(" ", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def equipment_score(value: object) -> int:
    text = normalize_text(value)
    if not text:
        return 0
    return len([part for part in text.split(",") if part.strip()])


def contains_any(value: object, terms: Iterable[str]) -> int:
    text = strip_accents(value)
    return int(any(term in text for term in terms))


def detect_trim(value: object) -> str:
    text = strip_accents(value)
    for label, pattern in TRIM_PATTERNS.items():
        if re.search(pattern, text):
            return label
    return "standard"


def has_equipment(value: object, needles: Iterable[str]) -> int:
    text = strip_accents(value)
    return int(any(strip_accents(needle) in text for needle in needles))


def add_market_reference_features(data: pd.DataFrame) -> pd.DataFrame:
    global_median = data["prix"].median()
    brand_model = data.groupby("brand_model")["prix"].median()
    brand_model_year = data.groupby(["brand_model", "annee"])["prix"].median()
    city_brand = data.groupby(["ville", "marque"])["prix"].median()

    data["brand_model_median_price"] = data["brand_model"].map(brand_model).fillna(global_median)
    data["brand_model_year_median_price"] = data.set_index(["brand_model", "annee"]).index.map(
        brand_model_year
    )
    data["brand_model_year_median_price"] = pd.Series(
        data["brand_model_year_median_price"], index=data.index
    ).fillna(data["brand_model_median_price"])
    data["city_brand_median_price"] = data.set_index(["ville", "marque"]).index.map(city_brand)
    data["city_brand_median_price"] = pd.Series(
        data["city_brand_median_price"], index=data.index
    ).fillna(global_median)
    return data


def remove_segment_outliers(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data["price_segment"] = pd.cut(
        data["prix"],
        bins=[0, 100_000, 250_000, 500_000, float("inf")],
        labels=["under_100k", "100k_250k", "250k_500k", "luxury_500k_plus"],
        include_lowest=True,
    )

    common_group = data.groupby("brand_model")["brand_model"].transform("size") >= 20
    q05 = data.groupby("brand_model")["prix"].transform(lambda values: values.quantile(0.05))
    q95 = data.groupby("brand_model")["prix"].transform(lambda values: values.quantile(0.95))
    segment_ok = (~common_group) | data["prix"].between(q05, q95)

    luxury_ok = data["is_luxury_vehicle"].eq(1) | data["prix"].le(1_200_000)
    very_low_ok = ~((data["prix"] < 25_000) & (data["annee"] >= 2010))
    suspicious_zero_km_ok = ~((data["kilometrage"] == 0) & (data["annee"] < CURRENT_YEAR - 1))
    km_rate_ok = data["km_per_year"].between(0, 120_000)

    return data[segment_ok & luxury_ok & very_low_ok & suspicious_zero_km_ok & km_rate_ok]


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    defaults = {
        "prix": "",
        "annee": "",
        "kilometrage": "",
        "puissance_fiscale": "",
        "nombre_portes": "",
        "marque": "",
        "modele": "",
        "ville": "",
        "carburant": "",
        "boite_vitesses": "",
        "etat": "",
        "premiere_main": "",
        "type_vendeur": "",
        "equipements": "",
        "titre": "",
        "description": "",
        "url": "",
        "origine": "",
    }
    for column, default in defaults.items():
        if column not in data.columns:
            data[column] = default

    for column in data.columns:
        if data[column].dtype == "object":
            data[column] = data[column].map(normalize_text)

    data["prix"] = data["prix"].map(parse_number)
    data["annee"] = data["annee"].map(parse_number)
    data["kilometrage"] = data["kilometrage"].map(parse_number)
    data["puissance_fiscale_num"] = data["puissance_fiscale"].map(parse_number)
    data["nombre_portes_num"] = data["nombre_portes"].map(parse_number)

    data["marque"] = data["marque"].map(lambda value: normalize_category(value))
    data["modele"] = data["modele"].map(lambda value: normalize_category(value))
    data["ville"] = data["ville"].map(lambda value: normalize_category(value))
    data["carburant"] = data["carburant"].map(lambda value: normalize_category(value, FUEL_MAP))
    data["boite_vitesses"] = data["boite_vitesses"].map(
        lambda value: normalize_category(value, TRANSMISSION_MAP)
    )
    data["etat"] = data["etat"].map(lambda value: normalize_category(value))
    data["premiere_main"] = data["premiere_main"].map(lambda value: normalize_category(value))
    data["type_vendeur"] = data["type_vendeur"].map(lambda value: normalize_category(value))
    data["brand_model"] = (data["marque"] + "_" + data["modele"]).str.strip("_")

    data["car_age"] = (CURRENT_YEAR - data["annee"]).clip(lower=0)
    age_for_rate = data["car_age"].replace(0, 1)
    data["km_per_year"] = data["kilometrage"] / age_for_rate
    data["equipment_score"] = data["equipements"].map(equipment_score)
    data["premium_brand"] = data["marque"].isin(PREMIUM_BRANDS).astype(int)
    combined_text = data["titre"].astype(str) + " " + data["description"].astype(str) + " " + data["equipements"].astype(str)
    data["trim_level"] = combined_text.map(detect_trim)
    data["luxury_score"] = combined_text.map(
        lambda value: sum(1 for term in LUXURY_TERMS if term in strip_accents(value))
    )
    data["is_luxury_vehicle"] = ((data["premium_brand"] == 1) | (data["luxury_score"] >= 2)).astype(int)
    origin_text = data["origine"].astype(str) + " " + combined_text
    data["is_imported"] = origin_text.map(lambda value: contains_any(value, ["importee", "importé", "import"] ))
    data["is_dedouanee"] = origin_text.map(lambda value: contains_any(value, ["dedouanee", "dédouanée", "dedouane"] ))
    data["is_ww_maroc"] = origin_text.map(lambda value: contains_any(value, ["ww au maroc", "ww maroc", "ww"] ))
    for column, needles in EQUIPMENT_PATTERNS.items():
        data[column] = combined_text.map(lambda value, terms=needles: has_equipment(value, terms))

    data = data.drop_duplicates(subset=["url"], keep="last")
    data = data.dropna(subset=["prix", "annee", "kilometrage"])
    data = data[
        (data["prix"].between(12_000, 5_000_000))
        & (data["annee"].between(1980, CURRENT_YEAR + 1))
        & (data["kilometrage"].between(0, 900_000))
    ]
    data = remove_segment_outliers(data)
    data = add_market_reference_features(data)

    fill_values = {
        "puissance_fiscale_num": data["puissance_fiscale_num"].median(),
        "nombre_portes_num": data["nombre_portes_num"].median(),
        "km_per_year": data["km_per_year"].median(),
        "brand_model_median_price": data["prix"].median(),
        "brand_model_year_median_price": data["prix"].median(),
        "city_brand_median_price": data["prix"].median(),
    }
    data = data.fillna(fill_values)
    return data.reset_index(drop=True)
