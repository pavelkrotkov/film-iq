"""Private discovery report I/O, with optional read-only accepted evidence."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from film_iq.discovery_batch import build_discoveries
from film_iq.discovery_order import Order
from film_iq.discovery_presentation import present_discovery
from film_iq.discovery_render import markdown


def discovery_command(
    cohort: Path | list[Path],
    snapshot: Path | None,
    database: Path | None,
    output_format: str,
    *,
    catalog: Path | None = None,
    order: Order = "source",
):
    records = _read_cohorts(cohort)
    personal = json.loads(snapshot.read_text()) if snapshot else None
    status_path = snapshot.with_suffix(snapshot.suffix + ".status") if snapshot else None
    status = json.loads(status_path.read_text()) if status_path and status_path.exists() else None
    if database is None:
        output = build_discoveries(records, personal, refresh_status=status)
    else:
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
            output = build_discoveries(records, personal, db=db, refresh_status=status)
    output = present_discovery(output, catalog, order)
    return (
        json.dumps(output, default=str, ensure_ascii=False, indent=2)
        if output_format == "json"
        else markdown(output)
    )


def _read_cohorts(cohort):
    paths = [cohort] if isinstance(cohort, Path) else cohort
    return [json.loads(path.read_text()) for path in paths]
