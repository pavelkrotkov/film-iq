"""Only accepted and permitted durable transitions become local changes."""

from datetime import datetime

from test_accept import AUDIT, pending
from test_acquisition import END, START, permit

from film_iq.changes import digest
from film_iq.ingest.accept import accept
from film_iq.ingest.acquisition import begin_attempt, finish_attempt


def test_accepted_source_change_survives_latest_failed_fetch(evidence_db):
    # A later fetch failure must not hide an independently accepted replacement.
    db = evidence_db
    pending(db)
    permit(db)
    now = datetime.fromisoformat(END)
    _, baseline = digest(db, None, now)
    attempt = begin_attempt(db, "s", START)
    finish_attempt(db, attempt, END, "success", revision_id="new")
    assert digest(db, baseline, now)[0]["source_changes"] == []
    accept(db, "new", AUDIT, previous_revision_id="rev")
    db.commit()
    attempt = begin_attempt(db, "s", END)
    finish_attempt(db, attempt, END, "error", error_code="timeout")
    result, acknowledged = digest(db, baseline, now)
    assert result["source_changes"][0]["revision_id"] == "new"
    assert result["source_changes"][0]["previous_revision_id"] == "rev"
    assert result["source_changes"][0]["url"] == "https://example.test/list"
    assert digest(db, acknowledged, now)[0]["source_changes"] == []
    permit(db, decision="blocked")
    result, hidden = digest(db, baseline, now)
    assert result["source_changes"] == [] and hidden == baseline
    permit(db)
    assert digest(db, hidden, now)[0]["source_changes"][0]["revision_id"] == "new"


def test_expired_source_permission_is_unknown_not_removal(evidence_db):
    pending(evidence_db)
    permit(evidence_db)
    now = datetime.fromisoformat(END)
    _, baseline = digest(evidence_db, None, now)
    permit(evidence_db, retain_until=END)
    assert digest(evidence_db, baseline, now)[1] == baseline
