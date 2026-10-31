"""Evidence reports and explicitly approved one-film Movary actions."""

import sqlite3
import sys
from collections.abc import Sequence

from film_iq.cli_parser import build_parser


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {"changes", "status"}:
        from importlib import import_module

        return import_module(f"film_iq.{argv[0]}_command").main(argv[1:])
    if argv and argv[0] in {"discover", "import-list", "refresh-movary", "acquisition-status"}:
        from film_iq.discovery_cli import main as discovery_main

        return discovery_main(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    return _execute(parser, args)


def _execute(parser, args) -> int:
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
            print(report_command(args.database, args.inputs, args.format, args.snapshot))
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            parser.error(str(error))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
