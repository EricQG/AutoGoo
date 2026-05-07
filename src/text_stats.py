"""Command-line text statistics tool.

Counts lines, words, characters, and top 10 most frequent words
in a given .txt file, with English stop word filtering.

Usage:
    python src/text_stats.py <path-to-txt-file>
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


STOP_WORDS: frozenset[str] = frozenset({
    "the", "a", "an", "is", "are", "was", "were",
    "and", "or", "but", "in", "on", "at", "to", "for", "of",
})


def count_lines(text: str) -> int:
    """Return the number of lines in *text*."""
    if not text:
        return 0
    return len(text.splitlines())


def count_words(text: str) -> int:
    """Return the total number of whitespace-separated tokens in *text*."""
    if not text:
        return 0
    return len(text.split())


def count_characters(text: str) -> int:
    """Return the total number of characters (including whitespace) in *text*."""
    return len(text)


def extract_words(text: str) -> list[str]:
    """Lower-case *text* and return all alphabetic word tokens.

    Tokens are extracted with the pattern ``[a-z]+`` so that punctuation
    and digits are stripped.
    """
    return re.findall(r"[a-z]+", text.lower())


def filter_stop_words(tokens: list[str]) -> list[str]:
    """Return *tokens* with stop words removed."""
    return [t for t in tokens if t not in STOP_WORDS]


def top_n_words(tokens: list[str], n: int = 10) -> list[tuple[str, int]]:
    """Return the *n* most common (word, count) pairs from *tokens*."""
    return Counter(tokens).most_common(n)


def analyze_text(file_path: str) -> dict:
    """Read a .txt file and return a dictionary of statistics.

    The returned dict has the following keys:
        file, lines, words, chars, top_words
    """
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")

    lines = count_lines(text)
    words = count_words(text)
    chars = count_characters(text)

    all_tokens = extract_words(text)
    filtered_tokens = filter_stop_words(all_tokens)
    top_words = top_n_words(filtered_tokens, n=10)

    return {
        "file": str(path.resolve()),
        "lines": lines,
        "words": words,
        "chars": chars,
        "top_words": top_words,
    }


def format_report(stats: dict) -> str:
    """Format the statistics dictionary into a human-readable string."""
    lines = [
        f"File:     {stats['file']}",
        f"Lines:    {stats['lines']}",
        f"Words:    {stats['words']}",
        f"Chars:    {stats['chars']}",
        "",
        "Top 10 words (stop words filtered):",
    ]
    for i, (word, count) in enumerate(stats["top_words"], start=1):
        lines.append(f"  {i:>2}. {word:<15s} {count}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point: parse argument and print report."""
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("Usage: python src/text_stats.py <path-to-txt-file>", file=sys.stderr)
        sys.exit(1)

    file_path = argv[0]
    stats = analyze_text(file_path)
    print(format_report(stats))


if __name__ == "__main__":
    main()
