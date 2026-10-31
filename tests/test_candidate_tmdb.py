"""TMDB candidates reuse partial-safe normalization without inventing tier or price."""

import pytest
from candidate_support import WORK
from offer_store_support import NOW

from film_iq.availability.candidate_tmdb import normalize


def payload(us):
    return {"id": 123, "results": {"US": us}}


def test_tmdb_valid_row_is_unconfirmed_and_price_plan_cut_unknown():
    result = normalize(
        WORK,
        payload(
            {
                "link": "https://example.test/watch",
                "flatrate": [{"provider_id": 7, "provider_name": "Fixture"}],
            }
        ),
        NOW,
    )
    item = result.assertions[0]
    assert result.status == "complete" and result.plan_scope is None
    assert item.opportunity.service == "tmdb:7"
    assert (item.price_minor, item.currency, item.opportunity.plan, item.opportunity.cut) == (
        None,
        None,
        None,
        None,
    )
    assert item.entitlement == "unconfirmed"


@pytest.mark.parametrize(
    "value",
    [
        None,
        {"id": True, "results": {"US": {}}},
        {"id": 999, "results": {}},
        {"id": 123, "results": {}},
    ],
)
def test_bad_work_or_missing_us_never_means_complete_empty(value):
    assert normalize(WORK, value or {}, NOW).status == "unknown"


def test_explicit_empty_and_partial_invalid_row_are_distinct():
    assert (
        normalize(WORK, payload({"link": "https://example.test/watch"}), NOW).status == "complete"
    )
    result = normalize(
        WORK,
        payload(
            {
                "link": "https://example.test/watch",
                "rent": [
                    {"provider_id": 7, "provider_name": "Fixture"},
                    {"provider_id": False, "provider_name": "Bad"},
                ],
            }
        ),
        NOW,
    )
    assert result.status == "partial" and len(result.assertions) == 1
