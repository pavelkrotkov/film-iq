"""Preview or explicitly run a bounded candidate manifest; no scheduler is installed."""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from film_iq.availability.candidate_models import ReviewedWork
from film_iq.availability.candidate_observe import MAPPERS
from film_iq.availability.candidate_run import run_candidates
from film_iq.storage import connect


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=tuple(MAPPERS), required=True)
    parser.add_argument(
        "--input", type=Path, required=True, help="Independently reviewed TMDB/IMDb crosswalk JSON"
    )
    parser.add_argument("--database", type=Path)
    parser.add_argument("--max-requests", type=int, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    try:
        works = [ReviewedWork(**item) for item in json.loads(args.input.read_text())]
        result = _run(args, works)
    except (OSError, ValueError, TypeError, PermissionError, sqlite3.Error):
        parser.exit(
            2, "Candidate run rejected or failed; check local inputs, policy and configuration.\n"
        )
    print(json.dumps(result, indent=2))
    return 0


def _run(args, works):
    if not args.live:
        return run_candidates(None, args.provider, works, max_requests=args.max_requests)
    if args.database is None or not args.database.is_file():
        raise ValueError("an existing policy database is required")
    with closing(connect(args.database)) as db:
        return run_candidates(db, args.provider, works, max_requests=args.max_requests, live=True)


if __name__ == "__main__":
    raise SystemExit(main())
