from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from auto_market_ai.catalog import load_catalog, to_listing_card
from auto_market_ai.preprocessing.cleaning import FUEL_MAP, TRANSMISSION_MAP, normalize_category


RECOMMENDER_FEATURES = [
    "prix",
    "annee",
    "kilometrage",
    "equipment_score",
    "premium_brand",
    "marque",
    "modele",
    "carburant",
    "boite_vitesses",
    "ville",
]


def _normalize_preference(key: str, value: object) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if key == "carburant":
        return normalize_category(text, FUEL_MAP)
    if key == "boite_vitesses":
        return normalize_category(text, TRANSMISSION_MAP)
    return normalize_category(text)


def apply_filters(data: pd.DataFrame, preferences: dict) -> pd.DataFrame:
    filtered = data.copy()
    budget = preferences.get("budget")
    if budget:
        filtered = filtered[filtered["prix"] <= float(budget) * 1.15]

    if preferences.get("annee_min"):
        filtered = filtered[filtered["annee"] >= int(preferences["annee_min"])]

    if preferences.get("kilometrage_max"):
        filtered = filtered[filtered["kilometrage"] <= int(preferences["kilometrage_max"])]

    for key in ("marque", "modele", "carburant", "boite_vitesses", "ville"):
        value = preferences.get(key)
        if not value:
            continue
        normalized = _normalize_preference(key, value)
        filtered = filtered[filtered[key].astype(str).str.lower() == normalized]

    return filtered


def recommend_cars(
    preferences: dict,
    catalog: pd.DataFrame | None = None,
    top_n: int = 10,
    slim: bool = True,
) -> list[dict]:
    data = catalog.copy() if catalog is not None else load_catalog()
    if data.empty:
        return []

    filtered = apply_filters(data, preferences)
    if filtered.empty:
        return []

    if preferences.get("marque"):
        preferred = _normalize_preference("marque", preferences["marque"])
        filtered["_brand_boost"] = (filtered["marque"].astype(str).str.lower() == preferred).astype(float)
    else:
        filtered["_brand_boost"] = 0.0

    budget = preferences.get("budget")
    query = {
        feature: preferences.get(
            feature,
            filtered[feature].median() if filtered[feature].dtype != "object" else "unknown",
        )
        for feature in RECOMMENDER_FEATURES
    }
    if budget and not preferences.get("prix"):
        query["prix"] = float(budget) * 0.92

    for key in ("marque", "modele", "carburant", "boite_vitesses", "ville"):
        if preferences.get(key):
            query[key] = _normalize_preference(key, preferences[key])

    sample = pd.concat([pd.DataFrame([query]), filtered[RECOMMENDER_FEATURES]], ignore_index=True)
    categorical = ["marque", "modele", "carburant", "boite_vitesses", "ville"]
    numeric = [feature for feature in RECOMMENDER_FEATURES if feature not in categorical]
    transformer = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", StandardScaler(), numeric),
        ]
    )
    pipeline = Pipeline([("features", transformer)])
    matrix = pipeline.fit_transform(sample)
    scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()

    ranked = filtered.copy()
    ranked["similarity_score"] = scores + ranked["_brand_boost"] * 0.1
    ranked = ranked.sort_values(["similarity_score", "prix"], ascending=[False, True]).head(top_n)
    records = ranked.drop(columns=["_brand_boost"], errors="ignore").to_dict(orient="records")
    if slim:
        return [to_listing_card(record) for record in records]
    return records
