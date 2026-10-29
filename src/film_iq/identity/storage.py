"""Store identity decisions using the issue #4 SQLite match contract."""

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from .models import Decision, Observation


def save(
    db: sqlite3.Connection,
    entry_id: str,
    revision_id: str,
    decision: Decision,
    supersedes: str | None = None,
) -> str:
    """Append a decision; the caller owns the transaction and film crosswalk."""
    if supersedes is not None:
        row = db.execute(
            "SELECT entry_id FROM match_decision WHERE id = ?", (supersedes,)
        ).fetchone()
        if row is None or row[0] != entry_id:
            raise ValueError("Superseded decision must belong to the same entry")
    film_id = None
    if decision.match is not None:
        row = db.execute(
            "SELECT id FROM film_index WHERE tmdb_id = ?", (decision.match,)
        ).fetchone()
        if row is None:
            raise ValueError("Matched TMDB ID must exist in film_index")
        film_id = row[0]
    decision_id = str(uuid4())
    evidence = json.dumps(
        {"observation": asdict(decision.observation), "evidence": decision.evidence}
    )
    db.execute(
        "INSERT INTO match_decision "
        "(id, entry_id, revision_id, film_id, candidates, method, version, confidence, reviewer, "
        "decision, decided_at, supersedes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            decision_id,
            entry_id,
            revision_id,
            film_id,
            json.dumps(decision.candidates),
            decision.method,
            decision.version,
            None,
            decision.reviewer,
            evidence,
            datetime.now(UTC).isoformat(),
            supersedes,
        ),
    )
    return decision_id


def load(db: sqlite3.Connection, decision_id: str) -> tuple[Decision, str | None]:
    """Recover a decision and its predecessor without altering source evidence."""
    row = db.execute(
        "SELECT m.candidates, f.tmdb_id, m.method, m.version, m.reviewer, m.decision, "
        "m.supersedes FROM match_decision m LEFT JOIN film_index f ON f.id = m.film_id "
        "WHERE m.id = ?",
        (decision_id,),
    ).fetchone()
    if row is None:
        raise ValueError("Unknown decision")
    candidates, match, method, version, reviewer, payload, supersedes = row
    data = json.loads(payload)
    return Decision(
        Observation(**data["observation"]),
        tuple(json.loads(candidates)),
        match,
        method,
        data["evidence"],
        reviewer,
        version,
    ), supersedes
