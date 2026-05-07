"""Batch CSV processor: merge multiple CSV files and compute statistics.

This script reads all CSV files from a given directory, merges them into a
single DataFrame, and outputs summary statistics including total row count
and mean values for numeric columns.
"""

from __future__ import annotations

import csv
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def discover_csv_files(data_dir: Path) -> List[Path]:
    """Return a sorted list of CSV file paths under *data_dir*.

    Args:
        data_dir: Directory to scan for CSV files.

    Returns:
        Sorted list of Path objects ending in ``.csv`` (case-insensitive).

    Raises:
        FileNotFoundError: If *data_dir* does not exist.
    """
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    csv_files: List[Path] = sorted(
        p for p in data_dir.iterdir() if p.suffix.lower() == ".csv"
    )
    return csv_files


def read_csv(file_path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """Read a CSV file and return its header and rows.

    Args:
        file_path: Path to the CSV file.

    Returns:
        A 2-tuple of (header, rows) where *header* is a list of column names
        and *rows* is a list of dicts keyed by column name.
    """
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header: List[str] = reader.fieldnames or []
        rows: List[Dict[str, str]] = list(reader)
    return header, rows


def merge_csv_files(file_paths: List[Path]) -> Tuple[List[str], List[Dict[str, str]]]:
    """Merge multiple CSV files with matching headers.

    All files must share the same set of column names (order is ignored during
    validation but the first file's ordering is used in the result).

    Args:
        file_paths: List of CSV file paths to merge.

    Returns:
        A 2-tuple of (merged_header, merged_rows).

    Raises:
        ValueError: If CSV files have mismatched headers.
    """
    merged_rows: List[Dict[str, str]] = []
    reference_header: Optional[List[str]] = None

    for fpath in file_paths:
        header, rows = read_csv(fpath)
        if reference_header is None:
            reference_header = header
        else:
            if set(header) != set(reference_header):
                raise ValueError(
                    f"Header mismatch in {fpath.name}: "
                    f"got {set(header)}, expected {set(reference_header)}"
                )
        merged_rows.extend(rows)

    return reference_header or [], merged_rows


def try_parse_float(value: str) -> Optional[float]:
    """Attempt to parse *value* as a float, returning ``None`` on failure.

    Args:
        value: Raw string value from CSV.

    Returns:
        A float if parsing succeeds, otherwise ``None``.
    """
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def compute_numeric_stats(
    rows: List[Dict[str, str]], header: List[str]
) -> Dict[str, Dict[str, Any]]:
    """Compute per-column statistics for numeric columns.

    A column is considered numeric if at least one of its values can be parsed
    as a float.

    Args:
        rows: Merged row dicts.
        header: Column names.

    Returns:
        A dict keyed by column name, each value being a dict with keys:
        ``mean``, ``min``, ``max``, ``count`` (non-null count).
    """
    stats: Dict[str, Dict[str, Any]] = {}

    for col in header:
        values: List[float] = []
        for row in rows:
            parsed = try_parse_float(row.get(col, ""))
            if parsed is not None:
                values.append(parsed)

        if values:
            stats[col] = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values),
            }

    return stats


def tabulate_results(
    total_rows: int,
    file_details: List[Tuple[str, int]],
    numeric_stats: Dict[str, Dict[str, Any]],
) -> str:
    """Format results as a human-readable string.

    Args:
        total_rows: Merged row count.
        file_details: List of (filename, row_count) tuples.
        numeric_stats: Per-column numeric stats from
            :func:`compute_numeric_stats`.

    Returns:
        A formatted string ready to print.
    """
    lines: List[str] = [
        "=" * 56,
        "  CSV Batch Merge - Summary Report",
        "=" * 56,
        "",
        f"  Input files:  {len(file_details)}",
        f"  Total rows:   {total_rows}",
        "",
        "  Files processed:",
    ]

    for name, count in file_details:
        lines.append(f"    - {name:<30s} {count:>4d} rows")

    if numeric_stats:
        lines.extend(
            [
                "",
                "  Numeric column statistics:",
                f"  {'Column':<20s} {'Mean':>12s} {'Min':>12s} {'Max':>12s} {'N':>6s}",
                "  " + "-" * 62,
            ]
        )
        for col, s in numeric_stats.items():
            lines.append(
                f"  {col:<20s} {s['mean']:>12.2f} {s['min']:>12.2f} "
                f"{s['max']:>12.2f} {s['count']:>6d}"
            )

    lines.append("")
    lines.append("=" * 56)
    return "\n".join(lines)


def main(data_dir_str: Optional[str] = None) -> None:
    """Entry point for the batch CSV processor.

    Args:
        data_dir_str: Optional override for the sample data directory.
                      Defaults to ``src/data_batch/sample_data/`` relative
                      to the script's parent.
    """
    start_time: float = time.time()

    script_dir: Path = Path(__file__).resolve().parent
    if data_dir_str:
        data_dir: Path = Path(data_dir_str)
    else:
        data_dir = script_dir / "sample_data"

    # Step 1: discover CSV files
    csv_files: List[Path] = discover_csv_files(data_dir)

    if not csv_files:
        print("No CSV files found. Exiting.")
        sys.exit(0)

    file_details: List[Tuple[str, int]] = []
    for fp in csv_files:
        _, rows = read_csv(fp)
        file_details.append((fp.name, len(rows)))

    # Step 2: merge
    header, merged_rows = merge_csv_files(csv_files)

    # Step 3: compute stats
    numeric_stats = compute_numeric_stats(merged_rows, header)

    # Step 4: output
    total_rows: int = len(merged_rows)
    report: str = tabulate_results(total_rows, file_details, numeric_stats)

    elapsed: float = time.time() - start_time
    print(report)
    print(f"\n  Elapsed: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
