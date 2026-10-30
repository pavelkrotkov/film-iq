"""Extract the frozen first 25 logical records of CNC's native visa CSV.

The source has a UTF-8 BOM, semicolon separators and a nine-cell header.
Values remain verbatim: trailing spaces, accents and unknown director labels
are source facts. Date is untyped; visa IDs are administrative identifiers.
No work identity, rank, year interpretation or critical evidence is inferred.
A separate source-row auditor supplies expectations; this module supplies none.
The pinned byte window and exact equality make partial extraction a failure.
"""

import csv
import hashlib
import io
import json
import time
from pathlib import Path

ROOT = Path(__file__).parent
HEADER = [
    "Titre",
    "Réalisation",
    "Production",
    "Format",
    "Date",
    "Nationalité",
    "N° de visa",
    "Décision",
    "Localisation du dossier visa",
]


def parse(body: bytes) -> list[dict]:
    """Require all 25 logical records, strict UTF-8/BOM and nine complete cells."""
    reader = csv.reader(
        io.StringIO(body.decode("utf-8-sig"), newline=""), delimiter=";", strict=True
    )
    if next(reader, None) != HEADER:
        raise ValueError("Unexpected CSV header")
    rows = list(reader)
    if len(rows) != 25 or any(len(row) != len(HEADER) for row in rows):
        raise ValueError("Incomplete or out-of-scope CSV window")
    return [observation(position, row) for position, row in enumerate(rows, 1)]


def observation(position: int, row: list[str]) -> dict:
    """Keep raw fields; row position is a locator, never a published rank."""
    return {
        "position": position,
        "raw_title": row[0],
        "raw_director": row[1],
        "raw_date": row[4],
        "category": row[3],
        "visa_id": row[6],
        "rank": None,
        "tie": False,
        "film_id": None,
    }


def check_rejection(body: bytes) -> bool:
    """A missing final source record must fail, rather than appear complete."""
    missing_final = b"\r\n".join(body.split(b"\r\n")[:-2]) + b"\r\n"
    try:
        parse(missing_final)
    except ValueError:
        return True
    raise AssertionError("Incomplete CSV accepted")


def run() -> dict:
    started = time.perf_counter()
    body = (ROOT / "source-window.csv").read_bytes()
    receipt = json.loads((ROOT / "source_receipt.json").read_text())
    if hashlib.sha256(body).hexdigest() != receipt["selection"]["window_sha256"]:
        raise ValueError("Source changed; new independent audit required")
    actual = parse(body)
    audit = json.loads((ROOT / "independent_audit.json").read_text())
    expected = audit["records"]
    exact = actual == expected
    if not exact:
        raise AssertionError("Source-row audit differs or is incomplete")
    return {
        "source_records_in_window": 25,
        "extracted_records": len(actual),
        "exact_records": len(actual),
        "complete": exact,
        "missing_final_rejected": check_rejection(body),
        "elapsed_seconds": time.perf_counter() - started,
        "scope": "development CSV supplement; not held-out or identity accuracy",
        "correction_minutes": None,
        "acquisition_labor_minutes": None,
        "resource_cost": None,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
