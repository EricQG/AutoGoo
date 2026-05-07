#!/usr/bin/env python3
"""Base64 streaming codec for large files.

Supports chunked encode/decode so that arbitrarily large files can be
processed with a fixed memory footprint.
"""

import argparse
import base64
import sys
import time
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 3 MiB -- multiple of 3 so that every chunk maps to whole base64 groups
# (3 bytes in -> 4 base64 chars out, no intra-chunk padding needed).
_ENCODE_CHUNK_SIZE: int = 3 * 1024 * 1024

# 4 MiB -- for reading base64 text input (any read size is fine; we handle
# group alignment in the decode loop).
_DECODE_CHUNK_SIZE: int = 4 * 1024 * 1024


# ---------------------------------------------------------------------------
# Streaming encode
# ---------------------------------------------------------------------------

def encode_stream(
    input_path: str,
    output_path: str,
) -> None:
    """Encode *input_path* (binary) to base64, writing to *output_path*.

    Reads the file in ``_ENCODE_CHUNK_SIZE`` blocks so that the whole file
    never has to fit in memory at once.
    """
    with open(input_path, "rb") as fin, open(output_path, "w") as fout:
        while True:
            chunk: bytes = fin.read(_ENCODE_CHUNK_SIZE)
            if not chunk:
                break
            encoded: bytes = base64.b64encode(chunk)
            fout.write(encoded.decode("ascii"))


# ---------------------------------------------------------------------------
# Streaming decode
# ---------------------------------------------------------------------------

# Whitespace characters that may appear inside base64 text (newlines from
# wrapping, spaces, tabs, etc.).
_WHITESPACE: set[str] = set(" \t\n\r\v\f")


def decode_stream(
    input_path: str,
    output_path: str,
) -> None:
    """Decode *input_path* (base64 text) back to binary, writing to *output_path*.

    Reads the file in chunks and carefully preserves base64 4-character group
    boundaries across chunk cuts so that decoding is always correct regardless
    of where the read happens to fall.
    """
    leftover: str = ""
    with open(input_path, "r") as fin, open(output_path, "wb") as fout:
        while True:
            chunk: str = fin.read(_DECODE_CHUNK_SIZE)
            if not chunk:
                # Flush any remaining buffered data
                if leftover:
                    decoded: bytes = base64.b64decode(leftover)
                    fout.write(decoded)
                break

            data: str = leftover + chunk

            # Count significant (non-whitespace) characters in *data*.
            sig_count: int = sum(1 for c in data if c not in _WHITESPACE)

            # Round down to the nearest multiple of 4 – this is how many
            # base64 characters we can safely decode from this chunk.
            usable: int = sig_count - (sig_count % 4)

            if usable == 0:
                # No complete base64 group yet; buffer everything.
                leftover = data
                continue

            # Walk through *data* character-by-character until we have
            # collected exactly *usable* significant characters.  The
            # split point is right after that character.
            count: int = 0
            split_at: int = 0
            for c in data:
                if c not in _WHITESPACE:
                    count += 1
                split_at += 1
                if count >= usable:
                    break

            to_decode: str = data[:split_at]
            leftover = data[split_at:]

            decoded = base64.b64decode(to_decode)
            fout.write(decoded)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Base64 encode/decode large files with streaming.",
    )
    parser.add_argument(
        "--mode",
        choices=["encode", "decode"],
        required=True,
        help="Operation mode",
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        required=True,
        help="Path to the input file",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        required=True,
        help="Path to the output file",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point: parse args and dispatch to the appropriate stream function."""
    args: argparse.Namespace = parse_args(argv)
    t0: float = time.perf_counter()

    if args.mode == "encode":
        encode_stream(args.input_path, args.output_path)
    else:
        decode_stream(args.input_path, args.output_path)

    elapsed: float = time.perf_counter() - t0
    in_size: int = Path(args.input_path).stat().st_size
    out_size: int = Path(args.output_path).stat().st_size

    print(
        f"[ok] {args.mode} {args.input_path} -> {args.output_path} "
        f"({in_size} bytes -> {out_size} bytes, {elapsed:.2f}s)",
    )


if __name__ == "__main__":
    main()
