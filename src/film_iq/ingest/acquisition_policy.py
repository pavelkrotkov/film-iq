"""Explicit source permission metadata; no implicit permission from public access."""

import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime

from film_iq.ingest.persist import SourcePolicy, _savepoint
from film_iq.ingest.persist_checks import _ensure_source


def utc_time(value: str) -> str:
    """Validate and normalize a timezone-aware time to sortable UTC."""
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError("a timezone-aware timestamp is required")
    return parsed.astimezone(UTC).isoformat()


def set_permission(
    db: sqlite3.Connection,
    policy: SourcePolicy,
    *,
    method: str,
    decision: str,
    evidence: str,
    reviewed_at: str,
    retain_until: str | None = None,
) -> None:
    """Record a reviewed permission decision before an acquisition can begin."""
    if not all(value.strip() for value in (*asdict(policy).values(), method, evidence)):
        raise ValueError("source policy, method and rights evidence are required")
    reviewed_at = utc_time(reviewed_at)
    retain_until = utc_time(retain_until) if retain_until is not None else None
    with _savepoint(db):
        _ensure_source(db, policy)
        db.execute(
            """INSERT INTO acquisition_permission VALUES (?,?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET method=excluded.method,
               decision=excluded.decision,evidence=excluded.evidence,
               reviewed_at=excluded.reviewed_at,retain_until=excluded.retain_until""",
            (policy.id, method, decision, evidence, reviewed_at, retain_until),
        )


def require_idle(db: sqlite3.Connection) -> None:
    if db.in_transaction:
        raise ValueError("finish the current transaction before recording an attempt")
    if not db.execute("PRAGMA foreign_keys").fetchone()[0]:
        raise ValueError("foreign keys must be enabled")
