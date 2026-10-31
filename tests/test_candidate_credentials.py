"""Official credential paths stay only in outbound requests, never receipts/errors."""

import json
from email.message import Message
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest
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


@pytest.mark.parametrize(
    "failure",
    [
        URLError("fixture-secret"),
        HTTPError(
            "https://example.test/?api_key=fixture-secret", 500, "fixture-secret", Message(), None
        ),
    ],
)
def test_transport_exception_cannot_leak_key(evidence_db, monkeypatch, failure):
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


def test_http_error_adapter_returns_status_not_authenticated_url(monkeypatch):
    opener = Mock()
    opener.open.side_effect = HTTPError(
        "https://example.test/?api_key=fixture-secret", 401, "fixture-secret", Message(), None
    )
    monkeypatch.setattr(candidate_transport, "build_opener", Mock(return_value=opener))
    result = candidate_transport.fetch(Mock())
    assert result == (401, b"", {})
    assert (
        candidate_transport._NoRedirect().redirect_request(
            None, None, 302, "", {}, "https://elsewhere.test"
        )
        is None
    )
