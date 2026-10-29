"""Persist complete inputs for replay of the provisional scoring algorithm.

The caller owns the transaction. Initialize the table separately from A1's
schema migration until the evidence and snapshot contracts are integrated.

Baseline uncertainty states are fixed Score defaults, reconstructed on replay.
They do not change input serialization or ranking, so existing v1 snapshot IDs
and numeric results remain reproducible without a version change.
"""

import hashlib
import json
import sqlite3
from dataclasses import asdict
from datetime import date

from film_iq.scoring import VERSION, Evidence, Score, score


def initialize(db: sqlite3.Connection) -> None:
    db.execute(
        "CREATE TABLE IF NOT EXISTS scoring_snapshot "
        "(id TEXT PRIMARY KEY, version TEXT NOT NULL, created_at TEXT NOT NULL, "
        "evidence TEXT NOT NULL)"
    )


def save(db: sqlite3.Connection, evidence: list[Evidence], created_at: str) -> str:
    """Save a canonical input set; repeated identical inputs are idempotent."""
    records = []
    for item in set(evidence):
        record = asdict(item)
        record["published"] = item.published.isoformat() if item.published else None
        for field in (
            "source_id",
            "document_id",
            "locator",
            "lineage_kind",
            "lineage",
            "author",
            "completeness",
            "rank_semantics",
        ):
            if record[field] is None:
                del record[field]
        records.append(json.dumps(record, sort_keys=True, separators=(",", ":")))
    payload = "[" + ",".join(sorted(records)) + "]"
    snapshot_id = hashlib.sha256((VERSION + "\n" + payload).encode()).hexdigest()
    db.execute(
        "INSERT OR IGNORE INTO scoring_snapshot VALUES (?, ?, ?, ?)",
        (snapshot_id, VERSION, created_at, payload),
    )
    return snapshot_id


def replay(db: sqlite3.Connection, snapshot_id: str) -> tuple[Score, ...]:
    """Reproduce a snapshot only with the algorithm version that created it."""
    row = db.execute(
        "SELECT version, evidence FROM scoring_snapshot WHERE id = ?", (snapshot_id,)
    ).fetchone()
    if row is None:
        raise KeyError(snapshot_id)
    version, payload = row
    if version != VERSION:
        raise ValueError(f"unsupported scoring version: {version}")
    records = json.loads(payload)
    for record in records:
        if record["published"] is not None:
            record["published"] = date.fromisoformat(record["published"])
        record["derivative_of"] = tuple(record["derivative_of"])
    return score([Evidence(**record) for record in records])
