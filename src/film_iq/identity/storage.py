"""Store identity decisions using the issue #4 SQLite match contract.

Source IDs are raw evidence: malformed text remains in the observation table
and permits an unresolved review, but cannot support an accepted match.
"""

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from .models import Candidate, Decision, Observation


def _validate_observation(
    db: sqlite3.Connection, entry_id: str, revision_id: str, decision: Decision
) -> None:
    row = db.execute(
        "SELECT raw_title, director, listed_year, raw_tmdb_id, raw_imdb_id FROM entry_observation "
        "WHERE entry_id = ? AND revision_id = ?",
        (entry_id, revision_id),
    ).fetchone()
    if row is None:
        raise ValueError("Decision observation must match the stored entry revision")
    try:
        tmdb_id = int(row[3]) if row[3] and row[3].strip() else None
    except ValueError:
        if decision.match is not None:
            raise ValueError("Malformed source TMDB ID requires an unresolved decision") from None
        tmdb_id = None
    if decision.observation != Observation(row[0], row[1], row[2], tmdb_id, row[4]):
        raise ValueError("Decision observation must match the stored entry revision")


def save(
    db: sqlite3.Connection,
    entry_id: str,
    revision_id: str,
    decision: Decision,
    supersedes: str | None = None,
) -> str:
    """Append a decision; the caller owns the transaction and film crosswalk."""
    _validate_supersedes(db, entry_id, supersedes)
    _validate_observation(db, entry_id, revision_id, decision)
    film_id = _film_id(db, decision.match)
    decision_id = str(uuid4())
    evidence = json.dumps(
        {
            "candidates": decision.candidates,
            "observation": asdict(decision.observation),
            "evidence": decision.evidence,
            "candidate_evidence": [asdict(candidate) for candidate in decision.candidate_evidence],
        }
    )
    existing = _automatic_replay(db, entry_id, revision_id, film_id, decision, evidence, supersedes)
    if existing is not None:
        return existing
    if not db.in_transaction:
        db.execute("BEGIN")
    db.execute("SAVEPOINT identity_save")
    try:
        preserve_review = _preserve_review(db, entry_id, revision_id, decision, supersedes)
        _insert_decision(
            db, decision_id, entry_id, revision_id, film_id, decision, evidence, supersedes
        )
        if not preserve_review:
            _update_current(db, entry_id, revision_id, decision_id, film_id)
    except Exception:
        db.execute("ROLLBACK TO identity_save")
        raise
    finally:
        db.execute("RELEASE identity_save")
    return decision_id


def _validate_supersedes(db, entry_id, supersedes):
    if supersedes is not None:
        row = db.execute(
            "SELECT entry_id FROM match_decision WHERE id = ?", (supersedes,)
        ).fetchone()
        if row is None or row[0] != entry_id:
            raise ValueError("Superseded decision must belong to the same entry")


def _preserve_review(db, entry_id, revision_id, decision, supersedes):
    # Unresolved reviews have no current_match row, so inspect the decision history.
    # A superseding decision ends protection for its predecessor. Automatic
    # evidence can still be recorded without replacing an active review.
    if decision.reviewer is not None or supersedes is not None:
        return False
    row = db.execute(
        "SELECT reviewer FROM match_decision WHERE entry_id = ? AND revision_id = ? "
        "AND NOT EXISTS (SELECT 1 FROM match_decision child "
        "WHERE child.supersedes = match_decision.id) "
        "AND reviewer IS NOT NULL ORDER BY rowid DESC LIMIT 1",
        (entry_id, revision_id),
    ).fetchone()
    return row is not None


def _automatic_replay(db, entry_id, revision_id, film_id, decision, evidence, supersedes):
    if decision.reviewer is not None or supersedes is not None:
        return None
    row = db.execute(
        "SELECT id FROM match_decision WHERE entry_id = ? AND revision_id = ? "
        "AND film_id IS ? AND candidates = ? AND method = ? AND version = ? "
        "AND reviewer IS NULL AND supersedes IS NULL ORDER BY rowid LIMIT 1",
        (entry_id, revision_id, film_id, evidence, decision.method, decision.version),
    ).fetchone()
    return row[0] if row else None


def _film_id(db: sqlite3.Connection, match: int | None) -> int | None:
    if match is None:
        return None
    row = db.execute("SELECT id FROM film_index WHERE tmdb_id = ?", (match,)).fetchone()
    if row is None:
        raise ValueError("Matched TMDB ID must exist in film_index")
    return row[0]


def _insert_decision(
    db, decision_id, entry_id, revision_id, film_id, decision, evidence, supersedes
):
    db.execute(
        "INSERT INTO match_decision "
        "(id, entry_id, revision_id, film_id, candidates, method, version, confidence, reviewer, "
        "decision, decided_at, supersedes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            decision_id,
            entry_id,
            revision_id,
            film_id,
            evidence,
            decision.method,
            decision.version,
            None,
            decision.reviewer,
            "accepted" if film_id is not None else "unresolved",
            datetime.now(UTC).isoformat(),
            supersedes,
        ),
    )


def _update_current(db, entry_id, revision_id, decision_id, film_id):
    if film_id is None:
        db.execute(
            "DELETE FROM current_match WHERE entry_id = ? AND revision_id = ?",
            (entry_id, revision_id),
        )
    else:
        db.execute(
            "INSERT INTO current_match (entry_id, revision_id, decision_id, film_id) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(entry_id, revision_id) DO UPDATE SET decision_id = excluded.decision_id, film_id = excluded.film_id",
            (entry_id, revision_id, decision_id, film_id),
        )


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
    stored = json.loads(candidates)
    data = json.loads(payload) if isinstance(stored, list) else stored
    candidate_ids = stored if isinstance(stored, list) else stored["candidates"]
    # Earlier decisions did not retain candidate snapshots. Keep them readable
    # without inventing evidence that was not recorded at decision time.
    return Decision(
        Observation(**data["observation"]),
        tuple(candidate_ids),
        match,
        method,
        data["evidence"],
        reviewer,
        version,
        tuple(
            Candidate(
                item["tmdb_id"],
                tuple(item["titles"]),
                item["director"],
                item["year"],
                item["imdb_id"],
            )
            for item in data.get("candidate_evidence", [])
        ),
    ), supersedes
