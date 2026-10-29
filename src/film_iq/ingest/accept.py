"""Explicitly accept an extraction using a human audit attestation."""

import sqlite3

from film_iq.ingest.accept_record import record_acceptance as _record_acceptance
from film_iq.ingest.audit import AuditAttestation, validate_audit
from film_iq.ingest.persist import _savepoint


def accept(
    db: sqlite3.Connection,
    revision_id: str,
    audit: AuditAttestation,
    *,
    previous_revision_id: str | None,
) -> None:
    """Promote a pending revision if its audit and expected current revision agree."""
    if not db.execute("PRAGMA foreign_keys").fetchone()[0]:
        raise ValueError("foreign keys must be enabled")
    validate_audit(audit)
    with _savepoint(db):
        _accept(db, revision_id, audit, previous_revision_id)


def _accept(
    db: sqlite3.Connection, revision_id: str, audit: AuditAttestation, previous: str | None
) -> None:
    row = db.execute(
        """SELECT r.list_id, r.validation_state, r.acceptance_state, d.fetch_state, s.outcome,
                  (SELECT count(*) FROM entry_observation WHERE revision_id=r.id)
           FROM extraction_revision r
           JOIN source_document d ON d.id=r.document_id
           JOIN source_run s ON s.id=r.run_id
           JOIN extraction_detail x ON x.revision_id=r.id
           JOIN extraction_fingerprint f ON f.revision_id=r.id
           WHERE r.id=?""",
        (revision_id,),
    ).fetchone()
    if row is None or row[1:5] != ("provisional", "pending", "success", "success"):
        raise ValueError("revision is not a complete pending extraction")
    list_id, *_, count = row
    if count != audit.expected_count:
        raise ValueError("audited count does not match stored observations")
    current = db.execute(
        "SELECT revision_id FROM current_extraction WHERE list_id=?", (list_id,)
    ).fetchone()
    if (current[0] if current else None) != previous:
        raise ValueError("current revision does not match explicit replacement")
    _record_acceptance(db, revision_id, audit, list_id, count, previous)
