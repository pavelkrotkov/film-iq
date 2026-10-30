"""Fictional responses: failed or incomplete observations never imply removal."""

import json
import sys
from pathlib import Path

import pytest

RESEARCH = Path(__file__).parents[1] / "docs/research/availability"
sys.path.insert(0, str(Path(__file__).parents[1]))
from docs.research.availability.observe import observe  # noqa: E402

FILM = {
    "key": "fixture",
    "stratum": "fictional",
    "tmdb_id": 123,
    "imdb_id": "tt123",
    "identity_evidence": "fictional independently reviewed IDs",
}


def response(data, status=200):
    return lambda request: (status, json.dumps(data).encode(), {"X-RateLimit-Remaining": "7"})


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
    assert all(row["entitlement"] == "unknown" for row in result["offers"])
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
    data = {"imdbId": "tt123", "showType": "movie", "streamingOptions": {"us": [row]}}
    result = observe(FILM, "motn", True, response(data))
    if not addon_id:
        assert result["state"] == "unknown" and "offers" not in result
        return
    assert result["state"] == "complete_response"
    assert result["offers"][0] == {
        "type": "addon",
        "service": "fictional",
        "link": "https://example.org/watch",
        "entitlement": "unknown",
        "addon": "extra",
        "source_details": {
            "expiresOn": None,
            "availableSince": None,
            "expiresSoon": True,
            "price": None,
        },
    }
