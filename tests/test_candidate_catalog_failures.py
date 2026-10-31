"""Unknown/partial public attempts preserve the last complete scoped baseline."""

import json
from datetime import timedelta
from unittest.mock import Mock

import pytest
from candidate_support import WORK, permit
from offer_store_support import NOW
from test_candidate_public_catalog import payload

from film_iq.availability.candidate_run import run_candidates
from film_iq.availability.fetch import Fetch
from film_iq.availability.state import read_state


@pytest.mark.parametrize(
    "provider,failure",
    [
        ("motn", "missing_us"),
        ("tmdb", "missing_us"),
        ("motn", "partial"),
        ("tmdb", "partial"),
    ],
)
def test_bad_public_response_does_not_advance_or_remove(
    evidence_db, monkeypatch, provider, failure
):
    permit(evidence_db, provider)
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fixture-secret")
    monkeypatch.setenv("MOVIE_OF_THE_NIGHT_API_KEY", "fixture-secret")
    # Failed responses retain the successful request's same public comparison context.
    status, broken = _broken(provider, failure)
    get = Mock(
        side_effect=[
            (200, json.dumps(payload(provider, True)).encode(), {}),
            (status, json.dumps(broken).encode(), {}),
        ]
    )
    for day in (0, 1):
        run_candidates(
            evidence_db,
            provider,
            [WORK],
            max_requests=1,
            live=True,
            now=NOW + timedelta(days=day),
            get=get,
        )
    state = read_state(
        evidence_db,
        Fetch(provider, 123, "US", NOW, "unknown", catalog_scope="public_country"),
        NOW + timedelta(days=1),
    )
    assert state["current"]["checked_at"] == NOW.isoformat()
    assert state["latest_attempt"]["status"] == ("partial" if failure == "partial" else "unknown")
    assert [e["kind"] for e in state["events"]] == ["source_first_seen"]


def _broken(provider, failure):
    broken = payload(provider, False)
    country_key = "streamingOptions" if provider == "motn" else "results"
    if failure == "missing_us":
        broken[country_key] = {}
    if failure == "partial":
        broken[country_key]["us" if provider == "motn" else "US"] = (
            [{"invalid": "row"}]
            if provider == "motn"
            else {"link": "https://example.test/watch", "rent": "invalid"}
        )
    return 200, broken
