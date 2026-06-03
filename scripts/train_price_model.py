from __future__ import annotations

import argparse
import json
from pathlib import Path

from auto_market_ai.ml.train import train_price_model


def main() -> int:
    parser = argparse.ArgumentParser(description="Train Auto Market AI price model.")
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--metrics", type=Path, default=None)
    args = parser.parse_args()

    kwargs = {}
    if args.dataset:
        kwargs["dataset_path"] = args.dataset
    if args.model:
        kwargs["model_path"] = args.model
    if args.metrics:
        kwargs["metrics_path"] = args.metrics

    metrics = train_price_model(**kwargs)
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
