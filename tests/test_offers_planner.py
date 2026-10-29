from datetime import UTC, date, datetime

import pytest

from film_iq.availability.tmdb import normalize
from film_iq.planning.monthly import Access, Film, compare

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


def test_bundle_compares_access_cost_overlap_and_expiry():
    films = [
        Film(1, "One", 90, 10),
        Film(2, "Two", 60, 8),
        Film(3, "Three", 60, 7),
        Film(4, "Watched", 30, 100, True),
    ]
    offers = [
        Access(1, 1, "subscription", "confirmed"),
        Access(1, 2, "subscription", "unconfirmed"),
        Access(2, 2, "subscription", "unconfirmed", expires=date(2026, 11, 1)),
        Access(3, 3, "rent", "unconfirmed", 300),
        Access(4, 2, "subscription", "confirmed"),
        Access(3, 2, "subscription", "unavailable_on_plan"),
    ]
    plans = compare(
        films, offers, {1}, [date(2026, 11, 1), date(2026, 11, 8)], 150, 2, 1000, {2: 700}
    )
    base, rental, service = plans
    assert [c.film.id for c in base.choices] == [1]
    assert rental.utility == 17 and rental.cost_cents == 300
    assert service.utility == 18 and service.cost_cents == 700 and service.total_minutes == 150
    assert [(c.film.id, c.viewing_date) for c in service.choices] == [
        (2, date(2026, 11, 1)),
        (1, date(2026, 11, 8)),
    ]
    assert "tentative" in service.assumptions
    assert compare(films, offers, {1}, [date(2026, 11, 8)], 150, 2, 500, {2: 700})[0].utility == 10
