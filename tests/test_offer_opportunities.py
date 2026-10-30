"""Synthetic offer-source disagreements remain independent from access certainty."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from film_iq.availability.access_check import first_seen_by_us, opportunities, purchase_ready
from film_iq.availability.assertion import Assertion
from film_iq.availability.opportunity import Opportunity

NOW = datetime(2026, 10, 30, tzinfo=UTC)


def test_sources_deduplicate_opportunity_but_keep_prices_and_timestamps():
    offer = Opportunity(1, "service", "subscription", "US", "basic", quality="HD")
    first = Assertion(offer, "a", NOW, "https://example.test/a", 500, "USD")
    other = replace(first, source="b", price_minor=700, checked_at=NOW + timedelta(days=1))
    grouped = opportunities((first, other, first))
    assert len(grouped) == 1 and grouped[offer] == (first, other)
    assert first_seen_by_us(grouped[offer]) == NOW
    assert first.asserted_added_on is None and first.asserted_expires_at is None
    assert not purchase_ready(first)
    assert (
        len(opportunities((first, replace(first, opportunity=replace(offer, plan="premium"))))) == 2
    )


def test_purchase_advice_requires_explicit_tier_price_cut_and_entitlement():
    offer = Opportunity(1, "service", "add-on", "US", "basic", "cinema", cut="theatrical")
    known = Assertion(
        offer, "a", NOW, "https://example.test/a", 500, "USD", "confirmed", "reviewed"
    )
    assert purchase_ready(known)
    for changed in (
        replace(known, entitlement="unconfirmed"),
        replace(known, work_status="cut_uncertain"),
        replace(known, price_minor=None),
        replace(known, currency=None),
        replace(known, opportunity=replace(offer, plan=None)),
        replace(known, opportunity=replace(offer, add_on=None)),
    ):
        assert not purchase_ready(changed)
