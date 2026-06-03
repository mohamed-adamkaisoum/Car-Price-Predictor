from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def read_log_lines(path: Path) -> list[str]:
    raw = path.read_bytes()
    encoding = "utf-16-le" if raw.count(b"\x00") > len(raw) * 0.1 else "utf-8"
    text = raw.decode(encoding, errors="replace").replace("\x00", "")
    return text.splitlines()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Show scrape progress from a CSV checkpoint.")
    parser.add_argument("--csv", type=Path, default=Path("data/avito_voitures_30000.csv"))
    parser.add_argument("--log", type=Path, default=Path("data/scrape_30000.log"))
    args = parser.parse_args()

    if args.csv.exists():
        print(f"rows: {len(pd.read_csv(args.csv))}")
        print(f"csv: {args.csv}")
    else:
        print(f"csv not found: {args.csv}")

    if args.log.exists():
        lines = read_log_lines(args.log)
        print("last log lines:")
        for line in lines[-10:]:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
