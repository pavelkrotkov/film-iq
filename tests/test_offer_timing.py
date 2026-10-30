"""Known offer intervals and explicit freshness constrain purchasing advice only."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from film_iq.availability.access_check import purchase_ready
from film_iq.availability.assertion import Assertion
from film_iq.availability.opportunity import Opportunity

NOW = datetime(2026, 10, 30, tzinfo=UTC)
DAY = timedelta(days=1)


def offer(**kwargs):
    return Assertion(
        Opportunity(1, "service", "rent", "US"),
        "source",
        NOW,
        "https://example.test",
        500,
        "USD",
        "confirmed",
        "reviewed",
        **kwargs,
    )


def test_expired_future_and_contradictory_intervals_cannot_qualify():
    assert not purchase_ready(offer(asserted_expires_at=NOW - DAY), now=NOW, max_age=DAY)
    assert not purchase_ready(offer(asserted_expires_at=NOW), now=NOW, max_age=DAY)
    assert not purchase_ready(offer(asserted_added_on=NOW + DAY), now=NOW, max_age=DAY)
    contradictory = offer(asserted_added_on=NOW + DAY, asserted_expires_at=NOW - DAY)
    assert not purchase_ready(contradictory, now=NOW, max_age=DAY)


def test_unknown_dates_stay_unknown_with_explicit_freshness():
    item = offer()
    assert purchase_ready(item, now=NOW, max_age=DAY)
    assert not purchase_ready(item, now=NOW + DAY * 2, max_age=DAY)
    assert not purchase_ready(item, now=NOW - DAY, max_age=DAY)
    assert item.asserted_added_on is item.asserted_expires_at is None
    assert purchase_ready(replace(item, asserted_expires_at=NOW + DAY), now=NOW, max_age=DAY)


def test_invalid_freshness_inputs_fail_explicitly():
    with pytest.raises(ValueError, match="age"):
        purchase_ready(offer(), now=NOW, max_age=-DAY)
    with pytest.raises(ValueError, match="timezone"):
        purchase_ready(offer(), now=NOW.replace(tzinfo=None), max_age=DAY)
