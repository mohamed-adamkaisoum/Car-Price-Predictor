from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from auto_market_ai.config import MODEL_PATH
from auto_market_ai.data.schema import ML_FEATURES
from auto_market_ai.preprocessing.cleaning import clean_dataset


def load_model(model_path: Path = MODEL_PATH):
    if not model_path.exists():
        raise FileNotFoundError(f"Modele introuvable: {model_path}")
    return joblib.load(model_path)


def apply_market_reference(features: pd.DataFrame, artifact: dict) -> pd.DataFrame:
    reference = artifact.get("market_reference") or {}
    if not reference:
        return features

    global_median = float(reference.get("global_median", 100_000))
    brand_model_ref = reference.get("brand_model_median_price", {})
    brand_model_year_ref = reference.get("brand_model_year_median_price", {})
    city_brand_ref = reference.get("city_brand_median_price", {})

    features = features.copy()
    features["brand_model_median_price"] = features["brand_model"].map(brand_model_ref).fillna(
        global_median
    )
    features["brand_model_year_median_price"] = [
        brand_model_year_ref.get(f"{row.brand_model}||{int(row.annee)}", fallback)
        for row, fallback in zip(
            features[["brand_model", "annee"]].itertuples(index=False),
            features["brand_model_median_price"],
        )
    ]
    features["city_brand_median_price"] = [
        city_brand_ref.get(f"{row.ville}||{row.marque}", global_median)
        for row in features[["ville", "marque"]].itertuples(index=False)
    ]
    return features


def prepare_inference_frame(records: list[dict], artifact: dict | None = None) -> pd.DataFrame:
    raw = pd.DataFrame(records)
    raw["prix"] = 100_000
    clean = clean_dataset(raw)
    features = clean.reindex(columns=ML_FEATURES)
    if artifact:
        features = apply_market_reference(features, artifact)
    return features


def predict_prices(records: list[dict], model_path: Path = MODEL_PATH) -> list[float]:
    artifact = load_model(model_path)
    model = artifact["model"] if isinstance(artifact, dict) and "model" in artifact else artifact
    features = prepare_inference_frame(records, artifact if isinstance(artifact, dict) else None)
    return [float(value) for value in model.predict(features)]


def predict_price_ranges(records: list[dict], model_path: Path = MODEL_PATH) -> list[dict[str, float]]:
    artifact = load_model(model_path)
    model = artifact["model"] if isinstance(artifact, dict) and "model" in artifact else artifact
    features = prepare_inference_frame(records, artifact if isinstance(artifact, dict) else None)
    predictions = [float(value) for value in model.predict(features)]
    residual_q10 = float(artifact.get("residual_q10", 0)) if isinstance(artifact, dict) else 0.0
    residual_q90 = float(artifact.get("residual_q90", 0)) if isinstance(artifact, dict) else 0.0
    ranges = []
    for prediction in predictions:
        lower = max(0.0, prediction + residual_q10)
        upper = max(lower, prediction + residual_q90)
        ranges.append(
            {
                "estimated_low": round(lower, 2),
                "estimated_price": round(prediction, 2),
                "estimated_high": round(upper, 2),
            }
        )
    return ranges
