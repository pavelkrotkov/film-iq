from test_accept import AUDIT, pending
from test_acquisition import END, START, permit

from film_iq.ingest.accept import accept
from film_iq.ingest.acquisition import begin_attempt, finish_attempt


def test_changed_extraction_requires_explicit_acceptance_after_successful_fetch(evidence_db):
    db = evidence_db
    pending(db)
    permit(db)
    first = begin_attempt(db, "s", START)
    finish_attempt(db, first, END, "success", revision_id="rev", cursor="old")
    changed = begin_attempt(db, "s", END)
    finish_attempt(db, changed, END, "success", revision_id="new", cursor="changed")
    assert db.execute("SELECT revision_id FROM current_extraction").fetchone() == ("rev",)
    accept(db, "new", AUDIT, previous_revision_id="rev")
    db.commit()
    again = begin_attempt(db, "s", END)
    finish_attempt(db, again, END, "success", revision_id="new", cursor="changed")
    assert db.execute("SELECT revision_id FROM current_extraction").fetchone() == ("new",)
    assert db.execute("SELECT count(*) FROM extraction_audit").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM entry_observation").fetchone() == (2,)
    assert db.execute("SELECT count(*) FROM acquisition_attempt").fetchone() == (3,)
