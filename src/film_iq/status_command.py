"""Read selected local state without network access or database-content changes."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from film_iq.status_inputs import catalog_status, inspect_input
from film_iq.status_personal import personal_status
from film_iq.status_run import run_status
from film_iq.status_sources import provider_status, source_status

ATTENTION = {"missing", "invalid", "stale", "expired", "not_yet_valid", "attention"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="film-iq status", description=__doc__)
    for name in ("run-status", "snapshot", "database", "catalog"):
        parser.add_argument(f"--{name}", type=Path)
    parser.add_argument("--now", type=datetime.fromisoformat, help="Timezone-aware assessment time")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    now = args.now or datetime.now(UTC)
    if now.utcoffset() is None:
        parser.error("assessment time must be timezone-aware")
    result = {
        "operations": inspect_input(args.run_status, run_status, now),
        "personal": inspect_input(args.snapshot, personal_status, now),
        "acquisition": inspect_input(args.database, source_status, now),
        "catalog": inspect_input(args.catalog, catalog_status, now),
        "provider_policies": inspect_input(args.database, provider_status, now),
    }
    print(json.dumps(result, indent=2) if args.format == "json" else _text(result))
    return int(any(item["state"] in ATTENTION for item in result.values()))


def _text(result: dict) -> str:
    lines = []
    for name, item in result.items():
        details = "; ".join(f"{key.replace('_', ' ')}: {value}" for key, value in item.items())
        lines.append(f"{name.replace('_', ' ').capitalize()}: {details}")
    return "\n".join([*lines, "Validation scope and remaining release gates: plan.md"])
