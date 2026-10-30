"""Strict manually curated rows; blank optional facts remain unknown."""

import csv
import io
from dataclasses import fields

from film_iq.ingest.curated_parse import parse_row
from film_iq.ingest.curated_row import CuratedRow
from film_iq.ingest.curated_validate import validate_ballot

COLUMNS = tuple(field.name for field in fields(CuratedRow))


def read_csv(body: str) -> tuple[CuratedRow, ...]:
    """Reject schema errors, extra cells, missing cells and duplicate positions."""
    reader = csv.DictReader(io.StringIO(body))
    if reader.fieldnames != list(COLUMNS):
        raise ValueError("CSV header must match the documented curated-list schema")
    rows = []
    for values in reader:
        if None in values or None in values.values():
            raise ValueError("CSV row has extra or missing cells")
        rows.append(parse_row(values))
    positions = [row.position for row in rows]
    if not rows or len(set(positions)) != len(positions):
        raise ValueError("nonempty selection with unique positions required")
    validate_ballot(rows)
    return tuple(rows)
