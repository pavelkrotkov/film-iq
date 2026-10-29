from datetime import UTC, datetime

import pytest

from film_iq.availability.tmdb import normalize

NOW = datetime(2026, 10, 29, tzinfo=UTC)


def test_tmdb_categories_uncertainty_and_completeness():
    provider = {"provider_id": 1, "provider_name": "Example Channel"}
    us = {
        "link": "https://example.org/movie",
        **{k: [provider] for k in ("flatrate", "rent", "buy", "free", "ads")},
    }
    result = normalize(42, {"id": 42, "results": {"US": us}}, NOW)
    assert result.status == "complete"
    assert {o.kind for o in result.offers} == {"subscription", "rent", "buy", "free", "ads"}
    assert all(
        o.entitlement == "unconfirmed" and o.source == "TMDB / JustWatch" for o in result.offers
    )
    assert normalize(42, None, NOW).status == "unknown"
    assert normalize(42, {"id": 42, "results": {}}, NOW).status == "unknown"
    us["unexpected_addon"] = [provider]
    us["buy"] = [{"provider_name": "bad"}]
    assert normalize(42, {"id": 42, "results": {"US": us}}, NOW).status == "partial"
    with pytest.raises(ValueError):
        normalize(42, None, datetime(2026, 1, 1))
