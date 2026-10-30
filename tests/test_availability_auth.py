"""Fictional API-key requests must not copy authenticated URLs into evidence."""

from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

import pytest
from test_availability_research import FILM, observe, response


@pytest.mark.parametrize("token", [None, "fictional-bearer"])
@pytest.mark.parametrize("status", [200, 401])
def test_tmdb_key_fallback_and_bearer_precedence(monkeypatch, token, status):
    monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("TMDB_API_KEY", "fictional-api-key")
    if token:
        monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", token)

    def get(request):
        assert parse_qs(urlsplit(request.full_url).query) == (
            {} if token else {"api_key": ["fictional-api-key"]}
        )
        assert request.get_header("Authorization") == (f"Bearer {token}" if token else None)
        return response({"id": 123, "results": {"US": {"link": "https://example.org"}}}, status)(
            request
        )

    result = observe(FILM, "tmdb", True, get)
    assert result["state"] == ("complete_response" if status == 200 else "unknown")
    assert result["endpoint"] == "https://api.themoviedb.org/3/movie/123/watch/providers"
    assert "fictional-" not in repr(result)


def test_tmdb_key_transport_exception_does_not_expose_url(monkeypatch):
    monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("TMDB_API_KEY", "fictional-api-key")

    def failed(request):
        raise URLError(request.full_url)

    result = observe(FILM, "tmdb", True, failed)
    assert result["state"] == "unknown" and "offers" not in result
    assert "api_key" not in repr(result) and "fictional-api-key" not in repr(result)
