"""Scope and timestamp checks use no real provider data."""

from dataclasses import replace
from datetime import datetime

import pytest
from test_offer_changes import NOW, snapshots

from film_iq.availability.reconcile import changes


def test_mismatched_source_country_or_time_cannot_create_removal():
    old, new = snapshots()
    with pytest.raises(ValueError, match="scopes"):
        changes(old, replace(new, source="other"))
    with pytest.raises(ValueError, match="scopes"):
        changes(old, replace(new, country="CA"))
    with pytest.raises(ValueError, match="backwards"):
        changes(new, old)
    with pytest.raises(ValueError, match="timezone"):
        replace(new, checked_at=datetime(2026, 10, 30))


def test_assertions_cannot_escape_their_scope_and_invalid_prices_fail():
    old, _ = snapshots()
    item = old.assertions[0]
    with pytest.raises(ValueError, match="scope"):
        replace(old, assertions=(replace(item, source="other"),))
    with pytest.raises(ValueError, match="price"):
        replace(item, price_minor=-1)
    with pytest.raises(ValueError, match="currency"):
        replace(item, currency="usd")
    with pytest.raises(ValueError, match="timezone"):
        replace(item, asserted_expires_at=NOW.replace(tzinfo=None))


def test_generic_service_claim_cannot_fill_verified_plan_scope():
    old, _ = snapshots()
    item = old.assertions[0]
    generic = replace(item, opportunity=replace(item.opportunity, plan=None))
    with pytest.raises(ValueError, match="plan"):
        replace(old, assertions=(generic,))
    unknown_plan = replace(old, assertions=(generic,), plan_scope=None)
    assert changes(unknown_plan, replace(unknown_plan, assertions=())) == ()
