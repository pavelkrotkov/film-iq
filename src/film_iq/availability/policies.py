"""Explicit reviewed policy registration and provider-data expiry enforcement."""

import sqlite3
from datetime import datetime

from film_iq.availability.codec import decode_policy, encode, timestamp
from film_iq.ingest.acquisition_policy import require_idle
from film_iq.retention import CachePolicy, status


def record_policy(db: sqlite3.Connection, policy: CachePolicy, now: datetime) -> None:
    """Only an explicit reviewed decision can enable or revoke source retention."""
    require_idle(db)
    payload = encode(policy)
    decode_policy(payload)
    with db:
        db.execute(
            "INSERT INTO offer_policy VALUES (?,?,?) ON CONFLICT(source) DO UPDATE "
            "SET payload=excluded.payload,reviewed_at=excluded.reviewed_at",
            (policy.source, payload, timestamp(now)),
        )


def policy_for(db: sqlite3.Connection, source: str) -> CachePolicy:
    row = db.execute("SELECT payload FROM offer_policy WHERE source=?", (source,)).fetchone()
    if row is None:
        raise PermissionError("source retention has no reviewed policy")
    return decode_policy(row[0])


def readable(db: sqlite3.Connection, source: str, now: datetime) -> bool:
    return status(policy_for(db, source), now) == "retain"


def purge_source(
    db: sqlite3.Connection, source: str, now: datetime, *, execute: bool = False
) -> tuple[str, ...]:
    """Preview expired rows or all terminated-source data; execution cascades events."""
    require_idle(db)
    policy = policy_for(db, source)
    terminal = status(policy, now) != "retain"
    rows = db.execute(
        "SELECT id FROM offer_fetch WHERE source=? AND (? OR expires_at<=?) ORDER BY id",
        (source, terminal, timestamp(now)),
    ).fetchall()
    identifiers = tuple(row[0] for row in rows)
    if execute:
        with db:
            db.executemany("DELETE FROM offer_fetch WHERE id=?", [(key,) for key in identifiers])
    return identifiers
