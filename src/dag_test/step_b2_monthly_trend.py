#!/usr/bin/env python3
"""Step B2: Read Step A's CSV output and compute monthly sales trends."""

import csv
import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

INPUT_DIR = Path(__file__).parent
CSV_PATH = INPUT_DIR / "sales_data.csv"
OUTPUT_PATH = INPUT_DIR / "monthly_trend.json"


def load_sales_data(path: Path) -> list[dict[str, Any]]:
    """Load CSV sales data into a list of dicts."""
    rows: list[dict[str, Any]] = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["amount"] = float(row["amount"])
            rows.append(row)
    return rows


def compute_monthly_trend(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Compute monthly sales aggregates."""
    monthly_data: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        month_key: str = row["date"][:7]  # YYYY-MM
        monthly_data[month_key].append(row["amount"])

    trend: dict[str, dict[str, float]] = {}
    for month, amounts in sorted(monthly_data.items()):
        trend[month] = {
            "order_count": len(amounts),
            "total_sales": round(sum(amounts), 2),
            "average_sale": round(sum(amounts) / len(amounts), 2),
        }
    return trend


def main() -> None:
    start_ts: str = datetime.now().isoformat()
    t0: float = time.time()

    rows: list[dict[str, Any]] = load_sales_data(CSV_PATH)
    trend: dict[str, dict[str, float]] = compute_monthly_trend(rows)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(trend, f, indent=2, ensure_ascii=False)

    elapsed: float = time.time() - t0

    print(f"Loaded {len(rows)} rows from {CSV_PATH}")
    print(f"Monthly trend written → {OUTPUT_PATH}")
    for month, t in trend.items():
        print(f"  {month}: {t['order_count']} orders, ${t['total_sales']:.2f}")
    print(f"Elapsed: {elapsed:.2f}s")

    # Log entry
    log_entry: str = (
        f"# Step B2: Monthly Trend\n\n"
        f"| Field | Value |\n"
        f"|------|-------|\n"
        f"| **Timestamp** | {start_ts} |\n"
        f"| **Status** | Completed |\n"
        f"| **Input** | {CSV_PATH} |\n"
        f"| **Output** | {OUTPUT_PATH} |\n"
        f"| **Elapsed** | {elapsed:.2f}s |\n\n"
        f"## Results\n"
    )
    for month, t in trend.items():
        log_entry += f"- **{month}**: {t['order_count']} orders, total ${t['total_sales']:.2f}, avg ${t['average_sale']:.2f}\n"

    log_entry += (
        f"\n## Key Decisions\n"
        f"1. Used YYYY-MM date truncation for monthly bucketing\n"
        f"2. JSON output for easy consumption by Step C\n"
        f"3. Included order count, total, and average per month\n"
    )
    print(f"\n--- Log ---\n{log_entry}")


if __name__ == "__main__":
    main()
