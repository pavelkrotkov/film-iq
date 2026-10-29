"""Read-only report command I/O, separate from report construction."""

import json
import sqlite3
from pathlib import Path

from film_iq.report import build_report
from film_iq.report_render import markdown


def report_command(database: Path, inputs_path: Path, output_format: str) -> str:
    inputs = json.loads(inputs_path.read_text())
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        output = build_report(db, inputs)
    if output_format == "json":
        return json.dumps(output, default=str, ensure_ascii=False, indent=2)
    return markdown(output)
