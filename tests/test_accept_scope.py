"""Acceptance changes only the audited revision, retaining other observation data."""

import pytest
from test_accept import AUDIT, pending

from film_iq.ingest.accept import accept


@pytest.mark.parametrize("historical_decision", ["accepted", "pending", "rejected"])
def test_observation_acceptance_is_revision_scoped(evidence_db, historical_decision):
    db = evidence_db
    pending(db)
    db.execute(
        "UPDATE entry_observation SET extraction_decision=? WHERE revision_id='rev'",
        (historical_decision,),
    )
    db.execute(
        "INSERT INTO extraction_revision SELECT 'unaccepted', source_id, list_id, "
        "document_id, run_id, 'v3', validation_state, acceptance_state "
        "FROM extraction_revision WHERE id='new'"
    )
    db.execute(
        "INSERT INTO entry_observation SELECT entry_id, source_id, list_id, 'unaccepted', "
        "raw_title, raw_context, original_title, listed_year, director, position, rank, tie, "
        "locator, extraction_decision, raw_imdb_id, raw_tmdb_id "
        "FROM entry_observation WHERE revision_id='new'"
    )
    untouched = "SELECT * FROM entry_observation WHERE revision_id != 'new' ORDER BY revision_id"
    before = db.execute(untouched).fetchall()
    accept(db, "new", AUDIT, previous_revision_id="rev")
    assert db.execute(
        "SELECT extraction_decision FROM entry_observation WHERE revision_id='new'"
    ).fetchall() == [("accepted",)]
    assert db.execute(untouched).fetchall() == before
    assert db.execute(
        "SELECT acceptance_state FROM extraction_revision WHERE id='unaccepted'"
    ).fetchone() == ("pending",)
