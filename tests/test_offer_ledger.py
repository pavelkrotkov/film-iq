"""Retained source observations are atomic, replayable and removal-safe."""

from datetime import timedelta

import pytest
from offer_store_support import NOW, fetch, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.availability.state import read_state
from film_iq.storage import connect


@pytest.mark.parametrize("failed_status", ["partial", "unknown"])
def test_reopen_replay_and_failed_fetch_do_not_remove_known_offers(
    evidence_db, tmp_path, failed_status
):
    prepare(evidence_db)
    first = save_fetch(evidence_db, fetch(), NOW)
    assert save_fetch(evidence_db, fetch(), NOW) == first
    evidence_db.close()
    with connect(tmp_path / "evidence.db") as db:
        save_fetch(db, fetch(1, status=failed_status, present=False), NOW + timedelta(days=1))
        state = read_state(db, fetch(), NOW + timedelta(days=1))
        assert state["latest_attempt"]["status"] == failed_status
        assert len(state["current"]["assertions"]) == 1
        assert [event["kind"] for event in state["events"]] == ["source_first_seen"]
        save_fetch(db, fetch(2, present=False), NOW + timedelta(days=2))
        save_fetch(db, fetch(2, present=False), NOW + timedelta(days=2))
        assert len(read_state(db, fetch(), NOW + timedelta(days=2))["events"]) == 2


def test_exact_plan_scopes_and_same_time_conflicts_are_preserved(evidence_db):
    prepare(evidence_db)
    save_fetch(evidence_db, fetch(), NOW)
    with pytest.raises(ValueError, match="conflicting complete"):
        save_fetch(evidence_db, fetch(present=False), NOW)
    assert len(read_state(evidence_db, fetch(), NOW)["current"]["assertions"]) == 1
    save_fetch(evidence_db, fetch(plan="Premium", present=False), NOW)
    assert not read_state(evidence_db, fetch(plan="Premium"), NOW)["current"]["assertions"]
