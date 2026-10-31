"""Derived events obey both inputs without expiring unrelated new observations."""

from datetime import timedelta

from offer_store_support import EXPIRY, NOW, fetch, prepare
from test_offer_retention_review import renew

from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import purge_source
from film_iq.availability.state import read_state


def test_removal_event_expires_with_old_input_without_expiring_new_baseline(evidence_db):
    """The new empty baseline remains live after its derived old content expires."""
    prepare(evidence_db)
    old = save_fetch(evidence_db, fetch(), NOW)
    renew(evidence_db)
    new = save_fetch(evidence_db, fetch(2, present=False), NOW + timedelta(days=2))
    assert len(read_state(evidence_db, fetch(), NOW + timedelta(days=2))["events"]) == 2
    state = read_state(evidence_db, fetch(), EXPIRY)
    assert state["events"] == []
    assert state["current"]["assertions"] == []
    assert purge_source(evidence_db, "fixture", EXPIRY) == (old,)
    purge_source(evidence_db, "fixture", EXPIRY, execute=True)
    assert evidence_db.execute("SELECT id FROM offer_fetch").fetchall() == [(new,)]
    assert evidence_db.execute("SELECT count(*) FROM offer_event").fetchone() == (0,)
