from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from auto_market_ai.config import CLEAN_DATA_PATH, METRICS_PATH, MODEL_PATH
from auto_market_ai.data.schema import ML_FEATURES, TARGET


CATEGORICAL_FEATURES = [
    "marque",
    "modele",
    "brand_model",
    "trim_level",
    "carburant",
    "boite_vitesses",
    "etat",
    "ville",
    "premiere_main",
    "type_vendeur",
]
NUMERIC_FEATURES = [feature for feature in ML_FEATURES if feature not in CATEGORICAL_FEATURES]


@dataclass
class CandidateResult:
    name: str
    model: Any
    predictions: np.ndarray
    metrics: dict[str, Any]


class LogTargetRegressor:
    def __init__(self, model: Any):
        self.model = model

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.model.fit(X, np.log1p(y))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.expm1(self.model.predict(X))


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5)),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
        ]
    )


def sklearn_log_pipeline(regressor: Any) -> TransformedTargetRegressor:
    pipeline = Pipeline(steps=[("preprocessor", build_preprocessor()), ("model", regressor)])
    return TransformedTargetRegressor(
        regressor=pipeline,
        func=np.log1p,
        inverse_func=np.expm1,
        check_inverse=False,
    )


def build_candidates() -> dict[str, Any]:
    candidates: dict[str, Any] = {
        "random_forest_log": sklearn_log_pipeline(
            RandomForestRegressor(
                n_estimators=320,
                min_samples_leaf=2,
                max_features="sqrt",
                random_state=42,
                n_jobs=-1,
            )
        ),
        "extra_trees_log": sklearn_log_pipeline(
            ExtraTreesRegressor(
                n_estimators=420,
                min_samples_leaf=2,
                max_features="sqrt",
                random_state=42,
                n_jobs=-1,
            )
        ),
    }

    try:
        from xgboost import XGBRegressor

        candidates["xgboost_log"] = sklearn_log_pipeline(
            XGBRegressor(
                n_estimators=650,
                max_depth=7,
                learning_rate=0.045,
                subsample=0.85,
                colsample_bytree=0.85,
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1,
            )
        )
    except Exception:
        pass

    try:
        from lightgbm import LGBMRegressor

        candidates["lightgbm_log"] = sklearn_log_pipeline(
            LGBMRegressor(
                n_estimators=900,
                learning_rate=0.035,
                num_leaves=63,
                subsample=0.85,
                colsample_bytree=0.85,
                random_state=42,
                n_jobs=-1,
                verbose=-1,
            )
        )
    except Exception:
        pass

    try:
        from catboost import CatBoostRegressor

        candidates["catboost_log"] = LogTargetRegressor(
            CatBoostRegressor(
                iterations=900,
                learning_rate=0.045,
                depth=8,
                loss_function="RMSE",
                random_seed=42,
                verbose=False,
                cat_features=CATEGORICAL_FEATURES,
                allow_writing_files=False,
            )
        )
    except Exception:
        pass

    return candidates


def regression_metrics(y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, predictions)),
        "rmse": float(mean_squared_error(y_true, predictions) ** 0.5),
        "r2": float(r2_score(y_true, predictions)),
    }


def segment_metrics(y_true: pd.Series, predictions: np.ndarray) -> dict[str, dict[str, float]]:
    frame = pd.DataFrame({"actual": y_true.to_numpy(), "predicted": predictions})
    segments = {
        "under_100k": frame["actual"] < 100_000,
        "100k_250k": frame["actual"].between(100_000, 250_000, inclusive="left"),
        "250k_500k": frame["actual"].between(250_000, 500_000, inclusive="left"),
        "luxury_500k_plus": frame["actual"] >= 500_000,
    }
    results: dict[str, dict[str, float]] = {}
    for name, mask in segments.items():
        segment = frame[mask]
        if len(segment) < 2:
            continue
        results[name] = {
            "rows": float(len(segment)),
            **regression_metrics(segment["actual"], segment["predicted"].to_numpy()),
        }
    return results


def evaluate_candidate(name: str, model: Any, X_train, X_test, y_train, y_test) -> CandidateResult:
    model.fit(X_train, y_train)
    predictions = np.maximum(model.predict(X_test), 0)
    metrics = {
        "rows": float(len(y_train) + len(y_test)),
        "train_rows": float(len(y_train)),
        "test_rows": float(len(y_test)),
        **regression_metrics(y_test, predictions),
        "segments": segment_metrics(y_test, predictions),
    }
    return CandidateResult(name=name, model=model, predictions=predictions, metrics=metrics)


def build_market_reference(data: pd.DataFrame) -> dict[str, Any]:
    return {
        "global_median": float(data[TARGET].median()),
        "brand_model_median_price": {
            str(key): float(value)
            for key, value in data.groupby("brand_model")[TARGET].median().items()
        },
        "brand_model_year_median_price": {
            f"{brand_model}||{int(year)}": float(value)
            for (brand_model, year), value in data.groupby(["brand_model", "annee"])[TARGET]
            .median()
            .items()
        },
        "city_brand_median_price": {
            f"{city}||{brand}": float(value)
            for (city, brand), value in data.groupby(["ville", "marque"])[TARGET].median().items()
        },
    }


def train_price_model(
    dataset_path: Path = CLEAN_DATA_PATH,
    model_path: Path = MODEL_PATH,
    metrics_path: Path = METRICS_PATH,
) -> dict[str, Any]:
    data = pd.read_csv(dataset_path)
    data = data.dropna(subset=[TARGET])
    if len(data) < 100:
        raise ValueError("Pas assez de donnees propres pour entrainer un modele fiable.")

    X = data[ML_FEATURES].copy()
    y = data[TARGET].copy()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=data["price_segment"]
    )

    results = [
        evaluate_candidate(name, model, X_train, X_test, y_train, y_test)
        for name, model in build_candidates().items()
    ]
    best = min(results, key=lambda result: result.metrics["mae"])
    residuals = y_test.to_numpy() - best.predictions

    all_metrics = {
        "best_model": best.name,
        "features": ML_FEATURES,
        "target": TARGET,
        "prediction_interval_residual_quantiles": {
            "q10": float(np.quantile(residuals, 0.10)),
            "q90": float(np.quantile(residuals, 0.90)),
        },
        "candidates": {result.name: result.metrics for result in results},
        "best_metrics": best.metrics,
    }

    artifact = {
        "model_name": best.name,
        "model": best.model,
        "features": ML_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "market_reference": build_market_reference(data),
        "residual_q10": all_metrics["prediction_interval_residual_quantiles"]["q10"],
        "residual_q90": all_metrics["prediction_interval_residual_quantiles"]["q90"],
        "metrics": all_metrics,
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)
    metrics_path.write_text(json.dumps(all_metrics, indent=2), encoding="utf-8")
    return all_metrics
