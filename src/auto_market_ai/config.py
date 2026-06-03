from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

RAW_DATA_PATH = DATA_DIR / "avito_voitures_30000.csv"
CLEAN_DATA_PATH = DATA_DIR / "processed" / "avito_voitures_clean.csv"
MODEL_PATH = MODELS_DIR / "price_model.joblib"
METRICS_PATH = REPORTS_DIR / "price_model_metrics.json"

CURRENT_YEAR = 2026
