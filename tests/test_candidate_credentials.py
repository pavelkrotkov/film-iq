"""Official credential paths stay only in outbound requests, never receipts/errors."""

import json
from unittest.mock import Mock
from urllib.error import URLError

from candidate_support import WORK, permit
from offer_store_support import NOW

from film_iq.availability import candidate_transport
from film_iq.availability.candidate_run import run_candidates


def test_tmdb_v3_fallback_and_bearer_preference(monkeypatch):
    monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("TMDB_API_KEY", "fixture-secret")
    request = candidate_transport.request("tmdb", WORK)
    assert request.full_url.endswith("?api_key=fixture-secret")
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fixture-bearer")
    preferred = candidate_transport.request("tmdb", WORK)
    assert "api_key" not in preferred.full_url
    assert preferred.get_header("Authorization") == "Bearer fixture-bearer"


def test_transport_exception_cannot_leak_key(evidence_db, monkeypatch):
    failure = URLError("fixture-secret")
    permit(evidence_db, "tmdb")
    monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("TMDB_API_KEY", "fixture-secret")
    result = run_candidates(
        evidence_db,
        "tmdb",
        [WORK],
        max_requests=1,
        live=True,
        now=NOW,
        get=Mock(side_effect=failure),
    )
    assert "fixture-secret" not in json.dumps(result)
    assert result["results"][0]["status"] == "unknown"
    assert "fixture-secret" not in "\n".join(evidence_db.iterdump())
