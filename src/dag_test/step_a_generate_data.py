#!/usr/bin/env python3
"""Step A: Generate a 1000-row random sales data CSV."""

import csv
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
CSV_PATH = OUTPUT_DIR / "sales_data.csv"

PRODUCTS = ["Widget-A", "Widget-B", "Gadget-X", "Gadget-Y", "Doohickey"]
REGIONS = ["North", "South", "East", "West"]
START_DATE = datetime(2025, 1, 1)

random.seed(42)


def generate_sales_data(num_rows: int = 1000) -> list[dict[str, str | float]]:
    """Generate random sales data rows.

    Each row contains: date, product, amount, region.
    """
    rows: list[dict[str, str | float]] = []
    for _ in range(num_rows):
        days_offset = random.randint(0, 364)  # 1 year span
        date = START_DATE + timedelta(days=days_offset)
        rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "product": random.choice(PRODUCTS),
            "amount": round(random.uniform(10.0, 500.0), 2),
            "region": random.choice(REGIONS),
        })
    return rows


def write_csv(rows: list[dict[str, str | float]], path: Path) -> None:
    """Write sales data to CSV file."""
    fieldnames = ["date", "product", "amount", "region"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    start_ts: str = datetime.now().isoformat()
    t0: float = time.time()

    rows: list[dict[str, str | float]] = generate_sales_data(1000)
    write_csv(rows, CSV_PATH)
    elapsed: float = time.time() - t0

    print(f"Generated {len(rows)} rows → {CSV_PATH}")
    print(f"Elapsed: {elapsed:.2f}s")

    # Log entry
    log_entry: str = (
        f"# Step A: Data Generation\n\n"
        f"| Field | Value |\n"
        f"|------|-------|\n"
        f"| **Timestamp** | {start_ts} |\n"
        f"| **Status** | Completed |\n"
        f"| **Rows Generated** | {len(rows)} |\n"
        f"| **Columns** | date, product, amount, region |\n"
        f"| **Output** | {CSV_PATH} |\n"
        f"| **Elapsed** | {elapsed:.2f}s |\n\n"
        f"## Key Decisions\n"
        f"1. Used seed=42 for reproducibility\n"
        f"2. 5 products × 4 regions × 365 days span for realistic distribution\n"
        f"3. Amount range $10–$500 with uniform distribution\n"
    )
    print(f"\n--- Log ---\n{log_entry}")


if __name__ == "__main__":
    main()
