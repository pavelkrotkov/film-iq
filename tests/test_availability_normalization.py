"""Fictional responses: failed or incomplete observations never imply removal."""

import pytest
from test_availability_research import FILM, observe, response


def test_tmdb_types_and_explicit_empty_region(monkeypatch):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fictional-secret")
    region = {
        "link": "https://example.org/watch",
        "ads": [{"provider_id": 7}],
        "rent": [{"provider_id": 7}],
        "buy": [{"provider_id": 7}],
    }
    result = observe(FILM, "tmdb", True, response({"id": 123, "results": {"US": region}}))
    assert {row["type"] for row in result["offers"]} == {"ads", "rent", "buy"}
    assert result["quota"] == {"X-RateLimit-Remaining": "7"}
    region = {"link": "https://example.org/watch"}
    empty = observe(FILM, "tmdb", True, response({"id": 123, "results": {"US": region}}))
    assert empty["state"] == "complete_response" and empty["offers"] == []


@pytest.mark.parametrize("addon_id", ["extra", None, ""])
def test_motn_addon_is_not_included_and_dates_remain_asserted(monkeypatch, addon_id):
    monkeypatch.setenv("MOVIE_OF_THE_NIGHT_API_KEY", "fictional-secret")
    row = {
        "type": "addon",
        "service": {"id": "fictional"},
        "addon": {"id": addon_id},
        "link": "https://example.org/watch",
        "expiresSoon": True,
    }
    data = {
        "imdbId": "tt123",
        "showType": "movie",
        "streamingOptions": {"us": [row | {"type": "subscription"}, row]},
    }
    result = observe(FILM, "motn", True, response(data))
    if not addon_id:
        assert result["state"] == "unknown" and "offers" not in result
        return
    assert result["state"] == "complete_response"
    offer = result["offers"][-1]
    assert (
        offer["type"],
        offer["addon"],
        offer["entitlement"],
        offer["source_details"]["expiresSoon"],
    ) == ("addon", "extra", "unknown", True)
