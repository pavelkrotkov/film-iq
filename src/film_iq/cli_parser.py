"""Shared CLI argument declaration."""

import argparse
from pathlib import Path

from film_iq import __version__


def build_parser():
    parser = argparse.ArgumentParser(prog="film-iq", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Show POC implementation and validation status")
    for name in ("discover", "import-list", "refresh-movary", "acquisition-status"):
        commands.add_parser(name, help="First-use MVP command; use COMMAND --help")
    report = commands.add_parser("report", help="Report current evidence and supplied US offers")
    report.add_argument("--database", type=Path, required=True)
    report.add_argument(
        "--inputs", type=Path, required=True, help="Catalog and provider snapshot JSON"
    )
    report.add_argument("--snapshot", type=Path, help="Fresh complete private Movary snapshot")
    report.add_argument("--format", choices=("markdown", "json"), default="markdown")
    sync = commands.add_parser("sync", help="Preview one Movary watchlist addition")
    sync.add_argument("--title", required=True)
    sync.add_argument("--tmdb-id", type=int, required=True)
    sync.add_argument("--execute", action="store_true")
    sync.add_argument("--approve", action="store_true", help="Approve this selected preview")
    return parser
