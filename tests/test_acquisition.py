import pytest

from film_iq.ingest.acquisition import acquisition_status, begin_attempt, finish_attempt
from film_iq.ingest.acquisition_policy import set_permission
from film_iq.ingest.persist import SourcePolicy

POLICY = SourcePolicy(
    "s",
    "Source",
    "https://example.test",
    "poll",
    "original",
    "public",
    "metadata only",
    "no copies",
    "cite source",
)
START = "2026-10-30T01:00:00+00:00"
END = "2026-10-30T01:01:00+00:00"


def permit(db, **changes):
    values = dict(
        method="manual factual records",
        decision="allowed",
        evidence="synthetic consent",
        reviewed_at=START,
    )
    values.update(changes)
    set_permission(db, POLICY, **values)
    db.commit()


def test_distinct_attempts_preserve_last_success_and_semantic_evidence(evidence_db):
    db = evidence_db
    permit(db)
    first = begin_attempt(db, "s", START)
    finish_attempt(db, first, END, "success", revision_id="rev", cursor="page-1")
    second = begin_attempt(db, "s", END)
    finish_attempt(db, second, END, "partial", error_code="incomplete")
    third = begin_attempt(db, "s", END)
    finish_attempt(db, third, END, "error", error_code="timeout")
    state = acquisition_status(db)[0]
    assert state["outcome"] == "error"
    assert (state["cursor"], state["succeeded_at"]) == ("page-1", END)
    assert db.execute(
        "SELECT previous_cursor FROM acquisition_attempt WHERE id=?", (third,)
    ).fetchone() == ("page-1",)
    assert db.execute("SELECT count(*) FROM entry_observation").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM extraction_revision").fetchone() == (1,)
    assert first != second != third


def test_permission_unknown_and_expired_are_blocked(evidence_db):
    db = evidence_db
    db.commit()
    with pytest.raises(PermissionError):
        begin_attempt(db, "s", START)
    permit(db, decision="blocked")
    with pytest.raises(PermissionError):
        begin_attempt(db, "s", START)
    permit(db, retain_until=START)
    with pytest.raises(PermissionError, match="expired"):
        begin_attempt(db, "s", END)
