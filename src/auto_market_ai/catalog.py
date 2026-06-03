from __future__ import annotations

from typing import Any

import pandas as pd

from auto_market_ai.config import CLEAN_DATA_PATH


def load_catalog(path=CLEAN_DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


LISTING_CARD_FIELDS = [
    "id",
    "titre",
    "marque",
    "modele",
    "annee",
    "kilometrage",
    "prix",
    "carburant",
    "boite_vitesses",
    "puissance_fiscale",
    "ville",
    "etat",
    "premiere_main",
    "nombre_portes",
    "equipements",
    "type_vendeur",
    "image_url",
    "url",
    "similarity_score",
]


def to_listing_card(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in LISTING_CARD_FIELDS if field in row}


def get_facets(catalog: pd.DataFrame | None = None) -> dict[str, Any]:
    data = catalog.copy() if catalog is not None else load_catalog()
    def facet_list(series: pd.Series, top_n: int) -> list[dict[str, Any]]:
        counts = series.astype(str).value_counts().head(top_n)
        return [{"value": str(index), "count": int(count)} for index, count in counts.items()]

    return {
        "brands": facet_list(data["marque"], 40),
        "cities": facet_list(data["ville"], 20),
        "fuels": sorted(data["carburant"].dropna().astype(str).unique().tolist()),
        "transmissions": sorted(data["boite_vitesses"].dropna().astype(str).unique().tolist()),
        "price": {
            "min": float(data["prix"].min()),
            "max": float(data["prix"].max()),
            "median": float(data["prix"].median()),
        },
        "total_listings": int(len(data)),
    }


def get_market_signals(catalog: pd.DataFrame | None = None) -> dict[str, Any]:
    data = catalog.copy() if catalog is not None else load_catalog()
    segments = {
        "under_100k": data["prix"] < 100_000,
        "100k_250k": data["prix"].between(100_000, 250_000, inclusive="left"),
        "250k_500k": data["prix"].between(250_000, 500_000, inclusive="left"),
        "luxury_500k_plus": data["prix"] >= 500_000,
    }
    by_segment = {}
    for name, mask in segments.items():
        segment = data[mask]
        if segment.empty:
            continue
        by_segment[name] = {
            "count": int(len(segment)),
            "median_price": float(segment["prix"].median()),
            "median_year": float(segment["annee"].median()),
            "median_km": float(segment["kilometrage"].median()),
        }

    top_brands = (
        data.groupby("marque")["prix"]
        .agg(count="count", median_price="median")
        .sort_values("count", ascending=False)
        .head(10)
        .reset_index()
    )
    auto_share = float((data["boite_vitesses"] == "automatique").mean())
    diesel_share = float((data["carburant"] == "diesel").mean())

    return {
        "total_listings": int(len(data)),
        "median_price": float(data["prix"].median()),
        "median_year": float(data["annee"].median()),
        "median_mileage": float(data["kilometrage"].median()),
        "automatic_share_pct": round(auto_share * 100, 1),
        "diesel_share_pct": round(diesel_share * 100, 1),
        "segments": by_segment,
        "top_brands": top_brands.to_dict(orient="records"),
        "dataset_path": str(CLEAN_DATA_PATH),
    }
