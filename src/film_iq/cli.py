"""Evidence reports and explicitly approved one-film Movary actions."""

import argparse
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from film_iq import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="film-iq", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Show POC implementation and validation status")
    report = commands.add_parser("report", help="Report current evidence and supplied US offers")
    report.add_argument("--database", type=Path, required=True)
    report.add_argument(
        "--inputs", type=Path, required=True, help="Catalog and provider snapshot JSON"
    )
    report.add_argument("--format", choices=("markdown", "json"), default="markdown")
    sync = commands.add_parser("sync", help="Preview one Movary watchlist addition")
    sync.add_argument("--title", required=True)
    sync.add_argument("--tmdb-id", type=int, required=True)
    sync.add_argument("--execute", action="store_true")
    sync.add_argument("--approve", action="store_true", help="Approve this selected preview")
    args = parser.parse_args(argv)
    if args.command == "status":
        print("film-iq POC modules available; see plan.md for validation status")
        return 0
    if args.command == "sync":
        from film_iq.sync_cli import sync_watchlist

        try:
            print(
                sync_watchlist(
                    args.title, args.tmdb_id, execute=args.execute, approved=args.approve
                )
            )
        except (PermissionError, ValueError) as error:
            parser.error(str(error))
        return 0
    if args.command == "report":
        from film_iq.report_command import report_command

        try:
            print(report_command(args.database, args.inputs, args.format))
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            parser.error(str(error))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
