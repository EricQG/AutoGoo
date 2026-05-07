#!/usr/bin/env python3
"""Step B1: Read Step A's CSV output and compute per-region statistics."""

import csv
import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

INPUT_DIR = Path(__file__).parent
CSV_PATH = INPUT_DIR / "sales_data.csv"
OUTPUT_PATH = INPUT_DIR / "region_stats.json"


def load_sales_data(path: Path) -> list[dict[str, Any]]:
    """Load CSV sales data into a list of dicts."""
    rows: list[dict[str, Any]] = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["amount"] = float(row["amount"])
            rows.append(row)
    return rows


def compute_region_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Compute sum, mean, and count of sales per region."""
    region_data: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        region_data[row["region"]].append(row["amount"])

    stats: dict[str, dict[str, float]] = {}
    for region, amounts in sorted(region_data.items()):
        stats[region] = {
            "count": len(amounts),
            "sum": round(sum(amounts), 2),
            "mean": round(sum(amounts) / len(amounts), 2),
            "min": round(min(amounts), 2),
            "max": round(max(amounts), 2),
        }
    return stats


def main() -> None:
    start_ts: str = datetime.now().isoformat()
    t0: float = time.time()

    rows: list[dict[str, Any]] = load_sales_data(CSV_PATH)
    stats: dict[str, dict[str, float]] = compute_region_stats(rows)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    elapsed: float = time.time() - t0

    print(f"Loaded {len(rows)} rows from {CSV_PATH}")
    print(f"Region stats written → {OUTPUT_PATH}")
    for region, s in stats.items():
        print(f"  {region}: count={s['count']}, sum={s['sum']:.2f}, mean={s['mean']:.2f}")
    print(f"Elapsed: {elapsed:.2f}s")

    # Log entry
    log_entry: str = (
        f"# Step B1: Region Statistics\n\n"
        f"| Field | Value |\n"
        f"|------|-------|\n"
        f"| **Timestamp** | {start_ts} |\n"
        f"| **Status** | Completed |\n"
        f"| **Input** | {CSV_PATH} |\n"
        f"| **Output** | {OUTPUT_PATH} |\n"
        f"| **Elapsed** | {elapsed:.2f}s |\n\n"
        f"## Results\n"
    )
    for region, s in stats.items():
        log_entry += f"- **{region}**: {s['count']} orders, total ${s['sum']:.2f}, avg ${s['mean']:.2f}\n"

    log_entry += (
        f"\n## Key Decisions\n"
        f"1. Used `defaultdict(list)` for clean aggregation\n"
        f"2. JSON output for easy machine consumption by Step C\n"
        f"3. Added min/max for richer reporting\n"
    )
    print(f"\n--- Log ---\n{log_entry}")


if __name__ == "__main__":
    main()
