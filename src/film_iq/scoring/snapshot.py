"""Canonical scoring inputs and policy for reproducible, versioned replay.

The caller owns the transaction; initialize separately from schema migrations.
V1 snapshots keep their frozen best-rank semantics. New snapshots record the
v2 source/window policy, so a caller cannot silently change replay selection.
"""

import hashlib
import json
import sqlite3
from dataclasses import asdict
from datetime import date

from film_iq.scoring import LEGACY_VERSION, VERSION, Evidence, Score, _score
from film_iq.scoring.policy import DEFAULT_POLICY, ScoringPolicy


def initialize(db: sqlite3.Connection) -> None:
    db.execute(
        "CREATE TABLE IF NOT EXISTS scoring_snapshot "
        "(id TEXT PRIMARY KEY, version TEXT NOT NULL, created_at TEXT NOT NULL, "
        "evidence TEXT NOT NULL)"
    )


def save(
    db: sqlite3.Connection,
    evidence: list[Evidence],
    created_at: str,
    *,
    policy: ScoringPolicy = DEFAULT_POLICY,
) -> str:
    """Save canonical unique inputs and declared policy; reruns are idempotent."""
    _score(evidence, policy, VERSION)
    records = sorted(
        json.dumps(asdict(item), sort_keys=True, default=str) for item in set(evidence)
    )
    payload = json.dumps(
        {"evidence": [json.loads(record) for record in records], "policy": asdict(policy)},
        sort_keys=True,
        separators=(",", ":"),
    )
    snapshot_id = hashlib.sha256((VERSION + "\n" + payload).encode()).hexdigest()
    db.execute(
        "INSERT OR IGNORE INTO scoring_snapshot VALUES (?, ?, ?, ?)",
        (snapshot_id, VERSION, created_at, payload),
    )
    return snapshot_id


def replay(db: sqlite3.Connection, snapshot_id: str) -> tuple[Score, ...]:
    """Replay both supported versions without reinterpreting historic results."""
    row = db.execute(
        "SELECT version, evidence FROM scoring_snapshot WHERE id = ?", (snapshot_id,)
    ).fetchone()
    if row is None:
        raise KeyError(snapshot_id)
    version, payload = row
    if version not in (VERSION, LEGACY_VERSION):
        raise ValueError(f"unsupported scoring version: {version}")
    document = json.loads(payload)
    records, policy = _inputs(document, version)
    for record in records:
        if record["published"] is not None:
            record["published"] = date.fromisoformat(record["published"])
        record["derivative_of"] = tuple(record["derivative_of"])
    return _score([Evidence(**record) for record in records], policy, version)


def _inputs(document, version: str):
    if version == LEGACY_VERSION:
        return document, ScoringPolicy()
    policy = ScoringPolicy(**{key: tuple(value) for key, value in document["policy"].items()})
    return document["evidence"], policy
