import pytest

from film_iq.ingest.accept import AuditAttestation, accept

AUDIT = AuditAttestation("Synthetic auditor", "synthetic audit notes", "2026-01-01Z", True, True, 1)


def pending(db):
    db.execute("INSERT INTO current_extraction (list_id, revision_id) VALUES ('list', 'rev')")
    db.execute(
        "INSERT INTO extraction_revision VALUES ('new', 's', 'list', 'doc', 'run', 'v2', 'provisional', 'pending')"
    )
    db.execute(
        "INSERT INTO extraction_detail VALUES ('new', 'v1', 'synthetic', 'one entry', 'review')"
    )
    db.execute("INSERT INTO extraction_fingerprint VALUES ('new', 'synthetic-hash')")
    db.execute(
        "INSERT INTO entry_observation SELECT entry_id, source_id, list_id, 'new', raw_title, raw_context, original_title, listed_year, director, position, rank, tie, locator, 'pending', raw_imdb_id, raw_tmdb_id FROM entry_observation WHERE revision_id='rev'"
    )


def test_explicit_promotion_preserves_history(evidence_db):
    db = evidence_db
    pending(db)
    accept(db, "new", AUDIT, previous_revision_id="rev")
    assert db.execute("SELECT revision_id FROM current_extraction").fetchone() == ("new",)
    assert db.execute(
        "SELECT validation_state, acceptance_state FROM extraction_revision WHERE id='rev'"
    ).fetchone() == ("valid", "accepted")
    assert db.execute(
        "SELECT auditor, evidence, independent_attested, complete_attested, expected_count, actual_count, previous_revision_id FROM extraction_audit"
    ).fetchone() == ("Synthetic auditor", "synthetic audit notes", 1, 1, 1, 1, "rev")
    assert db.execute("SELECT count(*) FROM entry_observation").fetchone() == (2,)


def test_stale_replacement_and_failed_fetch_remain_pending(evidence_db):
    db = evidence_db
    pending(db)
    with pytest.raises(ValueError, match="current revision"):
        accept(db, "new", AUDIT, previous_revision_id=None)
    db.execute("UPDATE source_document SET fetch_state='failed' WHERE id='doc'")
    with pytest.raises(ValueError, match="pending extraction"):
        accept(db, "new", AUDIT, previous_revision_id="rev")
    assert db.execute("SELECT count(*) FROM extraction_audit").fetchone() == (0,)
