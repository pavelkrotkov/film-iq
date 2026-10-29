"""Minimal CLI entry point; domain features are tracked in GitHub epics."""

import argparse
import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from film_iq import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="film-iq", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Show the bootstrap implementation status")
    report = commands.add_parser("report", help="Report current evidence and supplied US offers")
    report.add_argument("--database", type=Path, required=True)
    report.add_argument(
        "--inputs", type=Path, required=True, help="Catalog and provider snapshot JSON"
    )
    args = parser.parse_args(argv)
    if args.command == "status":
        print("film-iq bootstrap: CI and plan present; POC features are not implemented")
        return 0
    if args.command == "report":
        from film_iq.report import build_report

        try:
            inputs = json.loads(args.inputs.read_text())
            with sqlite3.connect(args.database.resolve().as_uri() + "?mode=ro", uri=True) as db:
                output = build_report(db, inputs)
            print(json.dumps(output, default=str, ensure_ascii=False, indent=2))
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            parser.error(str(error))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
