"""URL Health Checker — concurrently check HTTP status codes from a URL list file.

Usage:
    python src/url_health/url_health.py --input path/to/urls.txt
    python src/url_health/url_health.py --input urls.txt --timeout 10
"""

from __future__ import annotations

import argparse
import concurrent.futures
import http.client
import sys
import time
import urllib.error
import urllib.request
from typing import TextIO


def read_urls(filepath: str) -> list[str]:
    """Read a text file and return a list of non-empty stripped lines.

    Args:
        filepath: Path to the input file.

    Returns:
        List of URL strings.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with open(filepath, "r") as fh:  # noqa: PTH123 — standard lib only
        return [line.strip() for line in fh if line.strip()]


def _describe_status(code: int) -> str:
    """Map an HTTP status code to its standard description.

    Args:
        code: HTTP status code.

    Returns:
        Human-readable status description (e.g. "OK" for 200).
    """
    try:
        return http.client.responses[code]
    except KeyError:
        return "Unknown Status"


def check_url(url: str, timeout: int = 5) -> tuple[str, int | str, str]:
    """Perform an HTTP HEAD request and return (url, status_code, description).

    Falls back to GET if HEAD is not allowed.

    Args:
        url: The URL to check (scheme is added if missing).
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (url, status_code, description). On failure, status_code is
        "ERROR" and description holds the error message.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    req = urllib.request.Request(url, method="HEAD")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return url, resp.status, _describe_status(resp.status)
    except urllib.error.HTTPError as exc:
        # HEAD may be disallowed — fall back to GET for one attempt
        if exc.code in (405, 501):
            get_req = urllib.request.Request(url, method="GET")
            try:
                with urllib.request.urlopen(get_req, timeout=timeout) as resp:
                    return url, resp.status, _describe_status(resp.status)
            except urllib.error.HTTPError as get_exc:
                return url, get_exc.code, _describe_status(get_exc.code)
            except urllib.error.URLError as get_exc:
                return url, "ERROR", _describe_error(get_exc)
        return url, exc.code, _describe_status(exc.code)
    except urllib.error.URLError as exc:
        return url, "ERROR", _describe_error(exc)
    except OSError as exc:
        return url, "ERROR", str(exc)


def _describe_error(exc: urllib.error.URLError) -> str:
    """Return a short user-facing description of a URLError.

    Args:
        exc: The URLError instance.

    Returns:
        A string like "Timeout" or "DNS resolution failed".
    """
    msg = str(exc.reason) if exc.reason else "Unknown error"
    # Shorten common verbose messages
    if "Name or service not known" in msg or "Temporary failure in name resolution" in msg:
        return "DNS resolution failed"
    if "timed out" in msg.lower() or "timeout" in msg.lower():
        return "Timeout"
    if "Connection refused" in msg:
        return "Connection refused"
    if "No route to host" in msg:
        return "No route to host"
    return msg


def print_results(results: list[tuple[str, int | str, str]], output: TextIO = sys.stdout) -> None:
    """Print a formatted results table to *output*.

    Args:
        results: List of (url, status_code, description) tuples.
        output: Text stream to write to (defaults to stdout).
    """
    # Column widths
    url_w = max(len(r[0]) for r in results) if results else 4
    code_w = 11  # "Status Code"
    desc_w = 18  # "Status Description"

    sep = f"+{'-' * (url_w + 2)}+{'-' * (code_w + 2)}+{'-' * (desc_w + 2)}+"

    def write_line(url: str, code: int | str, desc: str) -> None:
        output.write(
            f"| {url:<{url_w}} | {str(code):>{code_w - 1}} | {desc:<{desc_w - 1}} |\n"
        )

    output.write(sep + "\n")
    write_line("URL", "Status Code", "Status Description")
    output.write(sep + "\n")

    for url, code, desc in results:
        write_line(url, code, desc)

    output.write(sep + "\n")
    output.flush()


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Concurrently check HTTP status codes for a list of URLs."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a text file containing one URL per line.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Request timeout in seconds (default: 5).",
    )
    return parser


def main() -> None:
    """Entry point — parse args, read URLs, check concurrently, print table."""
    parser = build_parser()
    args = parser.parse_args()

    urls = read_urls(args.input)

    if not urls:
        print("No URLs found in input file.", file=sys.stderr)
        sys.exit(1)

    results: list[tuple[str, int | str, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {
            executor.submit(check_url, url, args.timeout): url for url in urls
        }
        for future in concurrent.futures.as_completed(future_map):
            results.append(future.result())

    print_results(results)


if __name__ == "__main__":
    main()
