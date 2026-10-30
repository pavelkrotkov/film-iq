"""Explicit ballot links preserve people, original publishers and unknown identity."""

import sqlite3

from film_iq.ingest.acquisition_policy import utc_time
from film_iq.ingest.persist import _savepoint


def record_ballot(
    db: sqlite3.Connection,
    ballot_id: str,
    list_id: str,
    scope: str,
    *,
    contributor_id: str | None = None,
    contributor_name: str | None = None,
    original_ballot_id: str | None = None,
    published_at: str | None = None,
) -> None:
    """Known people share reviewed keys across publications; unknown people stay null."""
    if not all(value.strip() for value in (ballot_id, list_id, scope)):
        raise ValueError("ballot identity, list and scope are required")
    if original_ballot_id == ballot_id:
        raise ValueError("a ballot cannot derive from itself")
    published_at = utc_time(published_at) if published_at is not None else None
    values = (
        ballot_id,
        list_id,
        scope,
        contributor_id,
        contributor_name,
        original_ballot_id,
        published_at,
    )
    with _savepoint(db):
        db.execute(
            "INSERT INTO source_ballot VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING", values
        )
        if db.execute("SELECT * FROM source_ballot WHERE id=?", (ballot_id,)).fetchone() != values:
            raise ValueError("ballot metadata differs from the recorded identity")


def link_entry(db: sqlite3.Connection, entry_id: str, ballot_id: str) -> None:
    """Attach a stable entry to its ballot without silently replacing provenance."""
    with _savepoint(db):
        row = db.execute("SELECT list_id FROM list_entry WHERE id=?", (entry_id,)).fetchone()
        if row is None:
            raise ValueError("entry does not exist")
        db.execute(
            "INSERT INTO entry_ballot VALUES (?,?,?) ON CONFLICT(entry_id) DO NOTHING",
            (entry_id, row[0], ballot_id),
        )
        if db.execute(
            "SELECT ballot_id FROM entry_ballot WHERE entry_id=?", (entry_id,)
        ).fetchone() != (ballot_id,):
            raise ValueError("entry already belongs to a different ballot")
