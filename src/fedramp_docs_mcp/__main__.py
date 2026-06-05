"""CLI dispatch.

  fedramp-docs-mcp            # start stdio MCP server (default)
  fedramp-docs-mcp refresh    # pull latest FRMR snapshot from upstream
  fedramp-docs-mcp version    # print version
  fedramp-docs-mcp --help
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fedramp-docs-mcp",
        description=(
            "Unofficial MCP server exposing the public FedRAMP 20x machine-readable "
            "documentation. Run with no arguments to start the stdio MCP server."
        ),
    )
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("refresh", help="Pull the latest FRMR.documentation.json from upstream")
    sub.add_parser("version", help="Print server version")

    args = parser.parse_args(argv)

    if args.cmd == "refresh":
        from . import refresh

        return refresh.run()

    if args.cmd == "version":
        from . import __version__

        print(__version__)
        return 0

    from . import server

    server.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
