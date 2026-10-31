"""Canonical component snapshots leave historical critic v1/v2 replay unchanged."""

import hashlib
import json
import sqlite3
from dataclasses import asdict

from film_iq.recognition.reader import current_components
from film_iq.scoring import VERSION as CRITIC_VERSION
from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence

VERSION = "recognition-components-v1"


def document(db: sqlite3.Connection) -> dict:
    return {
        "version": VERSION,
        "critic_algorithm": CRITIC_VERSION,
        "critic_results": [asdict(result) for result in score(load_evidence(db))],
        "components": current_components(db),
        "calibration": "not established; no weighted blend",
    }


def save(db: sqlite3.Connection) -> str:
    """Freeze source/component links and exact original values; reruns are idempotent."""
    payload = json.dumps(document(db), sort_keys=True, ensure_ascii=False, default=str)
    identifier = hashlib.sha256((VERSION + "\n" + payload).encode()).hexdigest()
    db.execute(
        "INSERT OR IGNORE INTO recognition_snapshot VALUES (?,?,?)", (identifier, VERSION, payload)
    )
    return identifier


def replay(db: sqlite3.Connection, identifier: str) -> dict:
    row = db.execute(
        "SELECT version,payload FROM recognition_snapshot WHERE id=?", (identifier,)
    ).fetchone()
    if row is None:
        raise KeyError(identifier)
    if row[0] != VERSION:
        raise ValueError("unsupported recognition component snapshot version")
    return json.loads(row[1])
