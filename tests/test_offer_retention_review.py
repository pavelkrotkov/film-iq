"""Renewing permission cannot retain purged observations or derived old content."""

from dataclasses import replace
from datetime import timedelta

import pytest
from offer_store_support import EXPIRY, NOW, fetch, policy, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import purge_source, record_policy
from film_iq.availability.state import read_state


def renew(db):
    record_policy(
        db,
        replace(policy(allowed=True), expires_at=EXPIRY + timedelta(days=30)),
        NOW + timedelta(days=2),
    )


def test_renew_purge_cannot_resurrect_identical_historical_payload(evidence_db):
    """Renewal authorizes fresh checks, not the purged observation time."""
    prepare(evidence_db)
    save_fetch(evidence_db, fetch(), NOW)
    renew(evidence_db)
    purge_source(evidence_db, "fixture", EXPIRY, execute=True)
    with pytest.raises(ValueError, match="was purged"):
        save_fetch(evidence_db, fetch(), EXPIRY)
    assert read_state(evidence_db, fetch(), EXPIRY)["current"] is None
    save_fetch(evidence_db, fetch(31), NOW + timedelta(days=31))
    assert read_state(evidence_db, fetch(), NOW + timedelta(days=31))["current"] is not None
