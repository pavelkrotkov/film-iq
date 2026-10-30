"""Atomic completion of durable acquisition attempts."""

import sqlite3

from film_iq.ingest.acquisition_policy import require_idle, utc_time


def finish_attempt(
    db: sqlite3.Connection,
    attempt_id: str,
    finished_at: str,
    outcome: str,
    *,
    revision_id: str | None = None,
    cursor: str | None = None,
    error_code: str | None = None,
) -> None:
    """Only a complete successful fetch advances the durable cursor, not acceptance."""
    require_idle(db)
    finished_at = utc_time(finished_at)
    row = db.execute(
        "SELECT source_id,started_at,outcome FROM acquisition_attempt WHERE id=?", (attempt_id,)
    ).fetchone()
    if row is None or row[2] != "running" or finished_at < row[1]:
        raise ValueError("attempt is absent, finished, or finishes before its start")
    if outcome == "running":
        raise ValueError("a terminal outcome is required")
    if revision_id is not None and db.execute(
        "SELECT source_id FROM extraction_revision WHERE id=?", (revision_id,)
    ).fetchone() != (row[0],):
        raise ValueError("revision belongs to another source or is absent")
    with db:
        db.execute(
            """UPDATE acquisition_attempt SET finished_at=?,outcome=?,revision_id=?,
               cursor=?,error_code=? WHERE id=?""",
            (finished_at, outcome, revision_id, cursor, error_code, attempt_id),
        )
        if outcome == "success":
            db.execute(
                """INSERT INTO acquisition_cursor VALUES (?,?,?,?)
                   ON CONFLICT(source_id) DO UPDATE SET attempt_id=excluded.attempt_id,
                   cursor=excluded.cursor,succeeded_at=excluded.succeeded_at""",
                (row[0], attempt_id, cursor, finished_at),
            )
