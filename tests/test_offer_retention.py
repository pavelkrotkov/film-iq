"""Policy changes hide data immediately and explicit purges cascade its history."""

from dataclasses import replace
from datetime import timedelta

import pytest
from offer_store_support import EXPIRY, NOW, fetch, policy, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import purge_source, record_policy
from film_iq.availability.state import current_opportunities, read_state


def test_denial_and_termination_hide_then_purge_source_data(evidence_db):
    prepare(evidence_db)
    identifier = save_fetch(evidence_db, fetch(), NOW)
    record_policy(evidence_db, policy(allowed=False), NOW)
    assert read_state(evidence_db, fetch(), NOW)["current"] is None
    assert not current_opportunities(evidence_db, NOW)
    with pytest.raises(PermissionError):
        save_fetch(evidence_db, fetch(1), NOW + timedelta(days=1))
    record_policy(evidence_db, policy(allowed=False, terminated=True), NOW)
    assert purge_source(evidence_db, "fixture", NOW) == (identifier,)
    assert evidence_db.execute("SELECT count(*) FROM offer_fetch").fetchone() == (1,)
    purge_source(evidence_db, "fixture", NOW, execute=True)
    for table in ("offer_fetch", "offer_current", "offer_event"):
        assert evidence_db.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)


def test_renewal_does_not_extend_old_observation_retention(evidence_db):
    prepare(evidence_db)
    identifier = save_fetch(evidence_db, fetch(), NOW)
    renewed = replace(policy(allowed=True), expires_at=EXPIRY + timedelta(days=30))
    record_policy(evidence_db, renewed, NOW)
    assert read_state(evidence_db, fetch(), EXPIRY)["current"] is None
    assert purge_source(evidence_db, "fixture", EXPIRY) == (identifier,)
