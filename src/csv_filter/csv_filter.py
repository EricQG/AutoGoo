#!/usr/bin/env python3
"""CSV row filter: read CSV, filter rows by column comparison, output new CSV.

Usage:
    python csv_filter.py --input <path> --output <path> --column <name> --op <op> --value <val>
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse and validate CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Filter CSV rows by column comparison."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="Path to input CSV file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="Path to output CSV file.",
    )
    parser.add_argument(
        "--column",
        required=True,
        type=str,
        help="Column name to filter on.",
    )
    parser.add_argument(
        "--op",
        required=True,
        type=str,
        choices=[">", "<", "=="],
        help="Comparison operator (>, <, ==).",
    )
    parser.add_argument(
        "--value",
        required=True,
        type=str,
        help="Threshold value to compare against.",
    )
    return parser.parse_args(argv)


def compare_values(
    cell_value: str,
    threshold: str,
    operator: str,
) -> bool:
    """Compare a cell value against a threshold using the given operator.

    For ``>`` and ``<``, tries numeric comparison first, then falls back to
    lexicographic string comparison.  ``==`` always does exact string match.
    """
    if operator == "==":
        return cell_value == threshold

    # Numeric comparison (float covers both int and float columns).
    try:
        lhs = float(cell_value)
        rhs = float(threshold)
    except ValueError:
        lhs = cell_value
        rhs = threshold

    if operator == ">":
        return lhs > rhs
    # operator == "<"
    return lhs < rhs


def filter_csv(
    input_path: Path,
    output_path: Path,
    column: str,
    operator: str,
    threshold: str,
) -> int:
    """Read *input_path*, filter rows, write matching rows to *output_path*.

    Returns the number of rows written.
    """
    with open(input_path, newline="", encoding="utf-8") as f_in:
        reader: csv.DictReader = csv.DictReader(f_in)

        if reader.fieldnames is None:
            raise ValueError("Input CSV appears to be empty.")
        if column not in reader.fieldnames:
            raise ValueError(
                f"Column {column!r} not found. "
                f"Available columns: {reader.fieldnames}"
            )

        matched: list[dict[str, str]] = []
        for row in reader:
            if compare_values(row[column], threshold, operator):
                matched.append(row)

    with open(output_path, "w", newline="", encoding="utf-8") as f_out:
        writer: csv.DictWriter = csv.DictWriter(
            f_out, fieldnames=reader.fieldnames
        )
        writer.writeheader()
        writer.writerows(matched)

    return len(matched)


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = parse_args(argv)
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        count = filter_csv(
            input_path=input_path,
            output_path=output_path,
            column=args.column,
            operator=args.op,
            threshold=args.value,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {count} matching row(s) to {output_path}")


if __name__ == "__main__":
    main()
