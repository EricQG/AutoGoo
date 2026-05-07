"""A minimal HTTP file server using only the standard library.

Serves files from the current working directory over HTTP.
Supports a custom port via command-line argument.
"""

import argparse
import http.server
import logging
import sys
from typing import NoReturn


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list, defaults to sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Simple HTTP file server using http.server",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> NoReturn:
    """Start the HTTP file server.

    Args:
        argv: Argument list, defaults to sys.argv[1:].

    Raises:
        SystemExit: Always, when the server shuts down.
    """
    args = parse_args(argv)
    port: int = args.port

    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("", port), handler)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    logging.info("Serving HTTP on port %d", port)
    logging.info("Serving directory: %s", ".")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
