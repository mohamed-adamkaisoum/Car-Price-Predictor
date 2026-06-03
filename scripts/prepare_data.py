from __future__ import annotations

import argparse
from pathlib import Path

from auto_market_ai.preprocessing.pipeline import build_clean_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean Avito dataset for Auto Market AI.")
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    kwargs = {}
    if args.input:
        kwargs["input_path"] = args.input
    if args.output:
        kwargs["output_path"] = args.output

    clean = build_clean_dataset(**kwargs)
    print(f"Clean dataset rows: {len(clean)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
