"""Read-only report command I/O, separate from report construction."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from film_iq.report import build_report
from film_iq.report_render import markdown


def report_command(
    database: Path, inputs_path: Path, output_format: str, snapshot: Path | None = None
) -> str:
    inputs = json.loads(inputs_path.read_text())
    personal = json.loads(snapshot.read_text()) if snapshot else None
    status_path = snapshot.with_suffix(snapshot.suffix + ".status") if snapshot else None
    status = json.loads(status_path.read_text()) if status_path and status_path.exists() else None
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        output = build_report(db, inputs, snapshot=personal, refresh_status=status)
    if output_format == "json":
        return json.dumps(output, default=str, ensure_ascii=False, indent=2)
    return markdown(output)
