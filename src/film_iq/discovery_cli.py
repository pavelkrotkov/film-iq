"""First-use CLI seams reuse curated import, personal refresh and read-only reports."""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from film_iq.discovery_command import discovery_command
from film_iq.ingest.acquisition import acquisition_status


def main(argv: list[str]) -> int:
    if argv[0] == "refresh-movary":
        from film_iq.refresh_movary import main as refresh_main

        return refresh_main(argv[1:])
    parser = _parser(argv[0])
    args = parser.parse_args(argv[1:])
    try:
        output = _run(argv[0], args)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        parser.error(str(error))
    print(output)
    return 0


def _parser(command: str):
    parser = argparse.ArgumentParser(prog=f"film-iq {command}", description=__doc__)
    if command == "discover":
        parser.add_argument(
            "--cohort",
            type=Path,
            action="append",
            required=True,
            help="Complete curated import JSON; repeat for additional source ballots",
        )
        parser.add_argument(
            "--snapshot", type=Path, help="Private Movary snapshot; omit for unknown"
        )
        parser.add_argument("--database", type=Path, help="Read-only current accepted evidence")
        parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    elif command == "import-list":
        parser.add_argument("--csv", type=Path, required=True)
        parser.add_argument("--manifest", type=Path, required=True)
        parser.add_argument("--persist", type=Path)
    else:
        parser.add_argument("--database", type=Path, required=True)
    return parser


def _run(command: str, args) -> str:
    if command == "discover":
        return discovery_command(args.cohort, args.snapshot, args.database, args.format)
    if command == "import-list":
        from film_iq.ingest.curated_command import import_list_command

        return import_list_command(args.csv, args.manifest, args.persist)
    with closing(sqlite3.connect(args.database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        return json.dumps(acquisition_status(db), indent=2)
