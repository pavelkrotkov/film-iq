import sqlite3

import pytest
from test_acquisition import END, START, permit

from film_iq.ingest.acquisition import acquisition_status, begin_attempt, finish_attempt


@pytest.mark.parametrize(
    "outcome,revision,cursor",
    [
        ("success", None, None),
        ("error", "rev", None),
        ("partial", None, "bad"),
        ("invalid", None, None),
    ],
)
def test_invalid_finish_is_atomic(evidence_db, outcome, revision, cursor):
    db = evidence_db
    permit(db)
    attempt = begin_attempt(db, "s", START)
    with pytest.raises(sqlite3.IntegrityError):
        finish_attempt(db, attempt, END, outcome, revision_id=revision, cursor=cursor)
    assert acquisition_status(db)[0]["outcome"] == "running"
    assert db.execute("SELECT count(*) FROM acquisition_cursor").fetchone() == (0,)


def test_lifecycle_time_and_transaction_validation(evidence_db):
    db = evidence_db
    with pytest.raises(ValueError, match="transaction"):
        begin_attempt(db, "s", START)
    permit(db)
    with pytest.raises(ValueError, match="timezone"):
        begin_attempt(db, "s", "2026-10-30")
    attempt = begin_attempt(db, "s", END)
    with pytest.raises(ValueError, match="before"):
        finish_attempt(db, attempt, START, "error")
    finish_attempt(db, attempt, END, "unknown")
    with pytest.raises(ValueError, match="finished"):
        finish_attempt(db, attempt, END, "error")
