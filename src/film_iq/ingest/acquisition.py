"""Durable single-writer fetch attempts, distinct from semantic extraction runs."""

import json
import sqlite3
from uuid import uuid4

from film_iq.ingest.acquisition_finish import finish_attempt as finish_attempt
from film_iq.ingest.acquisition_policy import require_idle, utc_time


def begin_attempt(db: sqlite3.Connection, source_id: str, started_at: str) -> str:
    """Commit intent before I/O; an interrupted attempt remains visibly running."""
    require_idle(db)
    started_at = utc_time(started_at)
    permission = db.execute(
        "SELECT decision,retain_until,method,evidence,reviewed_at FROM acquisition_permission WHERE source_id=?",
        (source_id,),
    ).fetchone()
    if permission is None or permission[0] != "allowed":
        raise PermissionError("source method has no reviewed permission")
    if permission[1] is not None and permission[1] <= started_at:
        raise PermissionError("source retention permission has expired")
    attempt_id = str(uuid4())
    with db:
        db.execute(
            """INSERT INTO acquisition_attempt(id,source_id,started_at,outcome,permission_snapshot,previous_cursor)
               VALUES (?,?,?,'running',?,
               (SELECT cursor FROM acquisition_cursor WHERE source_id=?))""",
            (attempt_id, source_id, started_at, json.dumps(permission), source_id),
        )
    return attempt_id


def acquisition_status(db: sqlite3.Connection) -> list[dict[str, object]]:
    """Expose the latest attempt separately from the last successful cursor."""
    cursor = db.execute(
        """SELECT s.id AS source_id,a.id AS attempt_id,a.outcome,a.started_at,a.finished_at,
           a.error_code,c.cursor,c.succeeded_at,p.decision,p.retain_until
           FROM source s LEFT JOIN acquisition_attempt a ON a.rowid =
             (SELECT max(rowid) FROM acquisition_attempt WHERE source_id=s.id)
           LEFT JOIN acquisition_cursor c ON c.source_id=s.id
           LEFT JOIN acquisition_permission p ON p.source_id=s.id ORDER BY s.id"""
    )
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor]
