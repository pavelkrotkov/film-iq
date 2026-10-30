"""Fictional responses: failed or incomplete observations never imply removal."""

import json
import sys
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import URLError

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


def test_all_60_unresolved_candidates_are_retained_without_requests():
    cohort = json.loads((RESEARCH / "cohort.json").read_text())
    assert len(cohort) == len({row["key"] for row in cohort}) == 60
    records = [observe(row, "tmdb", True) for row in cohort]
    assert all(row["state"] == "unknown" and row["requests"] == 0 for row in records)


@pytest.mark.parametrize(
    "provider,env_key", [("tmdb", "TMDB_READ_ACCESS_TOKEN"), ("motn", "MOVIE_OF_THE_NIGHT_API_KEY")]
)
def test_credentials_and_live_flag_are_required(monkeypatch, provider, env_key):
    monkeypatch.delenv(env_key, raising=False)
    assert observe(FILM, provider, True)["requests"] == 0
    monkeypatch.setenv(env_key, "fictional-secret")
    assert observe(FILM, provider, False)["requests"] == 0


@pytest.mark.parametrize(
    "data,status",
    [
        ({"id": 123, "results": {}}, 200),
        ({"id": 123, "results": {"US": {}}}, 200),
        ({"id": 999, "results": {}}, 200),
        (
            {
                "id": 123,
                "results": {
                    "US": {"link": "https://example.org", "rent": [{"provider_id": 1}, {}]}
                },
            },
            200,
        ),
        ({"id": 123, "results": {}}, 429),
    ],
)
def test_tmdb_partial_failed_or_wrong_identity_has_no_offers(monkeypatch, data, status):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fictional-secret")
    result = observe(FILM, "tmdb", True, response(data, status))
    assert result["state"] == "unknown" and "offers" not in result
    assert result["requests"] == 1 and "fictional-secret" not in json.dumps(result)


@pytest.mark.parametrize("failure", [URLError("fictional-secret"), IncompleteRead(b"partial")])
def test_network_failure_and_missing_motn_region_remain_unknown(monkeypatch, failure):
    monkeypatch.setenv("MOVIE_OF_THE_NIGHT_API_KEY", "fictional-secret")

    def failed(request):
        raise failure

    assert observe(FILM, "motn", True, failed)["state"] == "unknown"
    data = {"imdbId": "tt123", "showType": "movie", "streamingOptions": {}}
    assert observe(FILM, "motn", True, response(data))["state"] == "unknown"
