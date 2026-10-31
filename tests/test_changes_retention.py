"""Only accepted and permitted durable transitions become local changes."""

from datetime import timedelta

import pytest
from offer_store_support import EXPIRY, NOW, fetch, prepare
from test_offer_retention_review import renew

from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import purge_source
from film_iq.changes import digest


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
