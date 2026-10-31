"""Local curated-list import: dry run unless --persist is explicitly supplied."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from film_iq.ingest.curated import import_list, load_manifest
from film_iq.ingest.curated_attempt import persist_attempt
from film_iq.storage import connect, migrate


def import_list_command(csv_path: Path, manifest_path: Path, database: Path | None = None) -> str:
    """Return the full selection and exact denominators; never mutate Movary."""
    body = csv_path.read_text(encoding="utf-8-sig")
    manifest = load_manifest(manifest_path)
    now = datetime.now(UTC).isoformat()
    # Validate rights, complete selection and identity attestations before opening storage.
    result = import_list(body, manifest, accessed_at=now)
    if database is not None:
        db = connect(database)
        try:
            migrate(db)
            result = persist_attempt(db, body, manifest, now)
        finally:
            db.close()
    return json.dumps(result, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--persist", type=Path, metavar="DATABASE")
    args = parser.parse_args()
    print(import_list_command(args.csv, args.manifest, args.persist))


if __name__ == "__main__":
    main()
