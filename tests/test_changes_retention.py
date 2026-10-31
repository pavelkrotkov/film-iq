"""Only accepted and permitted durable transitions become local changes."""

from datetime import timedelta

import pytest
from offer_store_support import EXPIRY, NOW, fetch, policy, prepare
from test_offer_retention_review import renew

from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import purge_source, record_policy
from film_iq.changes import digest


@pytest.mark.parametrize("changes", [{"allowed": False}, {"allowed": True, "terminated": True}])
def test_denied_or_terminated_offers_hide_payload_without_consuming_ids(evidence_db, changes):
    # Policy denial must not consume unseen IDs before they become readable again.
    db = evidence_db
    prepare(db)
    _, baseline = digest(db, None, NOW)
    save_fetch(db, fetch(), NOW)
    record_policy(db, policy(**changes), NOW)
    result, acknowledged = digest(db, baseline, NOW)
    assert result["offer_changes"] == [] and acknowledged == baseline
    record_policy(db, policy(allowed=True), NOW)
    assert len(digest(db, acknowledged, NOW)[0]["offer_changes"]) == 1


def test_expiry_purge_renewal_never_republishes_expired_inputs(evidence_db):
    db = evidence_db
    prepare(db)
    _, baseline = digest(db, None, NOW)
    save_fetch(db, fetch(), NOW)
    renew(db)
    save_fetch(db, fetch(2, present=False), NOW + timedelta(days=2))
    assert len(digest(db, baseline, NOW + timedelta(days=2))[0]["offer_changes"]) == 2
    assert digest(db, baseline, EXPIRY)[0]["offer_changes"] == []
    purge_source(db, "fixture", EXPIRY, execute=True)
    with pytest.raises(ValueError, match="purged"):
        save_fetch(db, fetch(), EXPIRY)
    assert digest(db, baseline, EXPIRY)[0]["offer_changes"] == []
    save_fetch(db, fetch(31), NOW + timedelta(days=31))
    assert len(digest(db, baseline, NOW + timedelta(days=31))[0]["offer_changes"]) == 1
