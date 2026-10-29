import sqlite3

import pytest
from test_accept import AUDIT, pending

from film_iq.ingest.accept import accept


def test_promotion_failure_rolls_back_and_preserves_caller_transaction(evidence_db):
    db = evidence_db
    pending(db)
    db.execute(
        "CREATE TRIGGER reject_promotion BEFORE UPDATE ON current_extraction BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END"
    )
    with pytest.raises(sqlite3.IntegrityError, match="synthetic failure"):
        accept(db, "new", AUDIT, previous_revision_id="rev")
    assert db.execute(
        "SELECT acceptance_state FROM extraction_revision WHERE id='new'"
    ).fetchone() == ("pending",)
    assert db.execute("SELECT count(*) FROM extraction_audit").fetchone() == (0,)
    assert db.execute("SELECT revision_id FROM current_extraction").fetchone() == ("rev",)
    db.rollback()
    assert db.execute("SELECT count(*) FROM extraction_revision WHERE id='new'").fetchone() == (0,)
