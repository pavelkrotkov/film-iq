"""A fresh batch wrapper cannot renew or resurrect an old assertion."""

from dataclasses import replace
from datetime import timedelta

import pytest
from offer_store_support import EXPIRY, NOW, fetch, prepare
from test_offer_retention_review import renew

from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import purge_source
from film_iq.availability.state import read_state


def test_new_wrapper_cannot_resurrect_purged_nested_assertion(evidence_db):
    prepare(evidence_db)
    original = fetch()
    save_fetch(evidence_db, original, NOW)
    renew(evidence_db)
    purge_source(evidence_db, "fixture", EXPIRY, execute=True)
    wrapper = replace(original, checked_at=NOW + timedelta(days=31))
    with pytest.raises(ValueError, match="was purged"):
        save_fetch(evidence_db, wrapper, wrapper.checked_at)
    assert read_state(evidence_db, original, wrapper.checked_at)["first_seen_by_us"] == []
    save_fetch(evidence_db, fetch(31), wrapper.checked_at)
    current = read_state(evidence_db, original, wrapper.checked_at)
    assert current["first_seen_by_us"][0]["first_seen_by_us"] == wrapper.checked_at.isoformat()


def test_cached_nested_input_keeps_frozen_deadline_before_purge(evidence_db):
    prepare(evidence_db)
    original = fetch()
    save_fetch(evidence_db, original, NOW)
    renew(evidence_db)
    wrapper = replace(original, checked_at=NOW + timedelta(days=3))
    identifier = save_fetch(evidence_db, wrapper, wrapper.checked_at)
    deadline = evidence_db.execute(
        "SELECT expires_at FROM offer_fetch WHERE id=?", (identifier,)
    ).fetchone()
    assert deadline == (EXPIRY.isoformat(),)
    assert read_state(evidence_db, original, EXPIRY)["current"] is None
    expired_wrapper = replace(original, checked_at=NOW + timedelta(days=31))
    with pytest.raises(ValueError, match="cached assertion retention expired"):
        save_fetch(evidence_db, expired_wrapper, expired_wrapper.checked_at)
