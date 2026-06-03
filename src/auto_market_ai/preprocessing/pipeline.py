from __future__ import annotations

from pathlib import Path

import pandas as pd

from auto_market_ai.config import CLEAN_DATA_PATH, RAW_DATA_PATH
from auto_market_ai.preprocessing.cleaning import clean_dataset


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset introuvable: {path}")
    return pd.read_csv(path)


def build_clean_dataset(
    input_path: Path = RAW_DATA_PATH,
    output_path: Path = CLEAN_DATA_PATH,
) -> pd.DataFrame:
    raw = load_raw_data(input_path)
    clean = clean_dataset(raw)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(output_path, index=False, encoding="utf-8-sig")
    return clean
