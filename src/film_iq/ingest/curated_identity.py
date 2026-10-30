"""Reviewed curated IDs use the existing reversible identity-decision ledger."""

import sqlite3

from film_iq.identity.models import Decision, Observation
from film_iq.identity.storage import save
from film_iq.ingest.curated_csv import CuratedRow


def record_identity(db: sqlite3.Connection, entry: str, revision: str, row: CuratedRow) -> None:
    if row.tmdb_id is None:
        return
    existing = db.execute(
        "SELECT 1 FROM match_decision WHERE entry_id=? AND revision_id=?", (entry, revision)
    ).fetchone()
    if existing:
        return
    db.execute("INSERT INTO film_index (tmdb_id) VALUES (?) ON CONFLICT DO NOTHING", (row.tmdb_id,))
    decision = Decision(
        Observation(row.raw_title, row.director, row.year, row.tmdb_id),
        (row.tmdb_id,),
        row.tmdb_id,
        "manual",
        row.identity_evidence or "",
        row.identity_reviewer,
    )
    save(db, entry, revision, decision)
