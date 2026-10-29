"""Record an audit and update the current extraction within the caller's savepoint."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from film_iq.ingest.audit import AuditAttestation


def record_acceptance(
    db: sqlite3.Connection,
    revision_id: str,
    audit: AuditAttestation,
    list_id: str,
    count: int,
    previous: str | None,
) -> None:
    db.execute(
        "INSERT INTO extraction_audit VALUES (?,?,?,?,?,?,?,?,?)",
        (
            revision_id,
            audit.auditor,
            audit.evidence,
            audit.audited_at,
            1,
            1,
            audit.expected_count,
            count,
            previous,
        ),
    )
    db.execute(
        "UPDATE extraction_revision SET validation_state='valid', acceptance_state='accepted' WHERE id=?",
        (revision_id,),
    )
    db.execute(
        "UPDATE entry_observation SET extraction_decision='accepted' WHERE revision_id=?",
        (revision_id,),
    )
    db.execute(
        "INSERT INTO current_extraction (list_id, revision_id) VALUES (?,?) "
        "ON CONFLICT(list_id) DO UPDATE SET revision_id=excluded.revision_id",
        (list_id, revision_id),
    )
