"""Both TMDB credentials authenticate requests without entering evidence."""

from urllib.parse import parse_qs, urlsplit

import pytest
from test_history_research import CANDIDATE, FILM, lookup, response

from docs.research.history import search


@pytest.mark.parametrize("bearer", ["bearer-secret", ""])
def test_authentication_and_redacted_failure(monkeypatch, bearer):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", bearer)
    monkeypatch.setenv("TMDB_API_KEY", "key-secret")
    requests = []

    def open_request(request, timeout):
        requests.append(request)
        raise TimeoutError(request.full_url)

    monkeypatch.setattr(search, "urlopen", open_request)
    result = lookup(FILM, live=True)
    request = requests[0]
    params = parse_qs(urlsplit(request.full_url).query)
    assert request.get_header("Authorization") == (f"Bearer {bearer}" if bearer else None)
    assert params.get("api_key") == (None if bearer else ["key-secret"])
    assert result["failure"] == {"phase": "transport", "type": "TimeoutError"}
    assert "key-secret" not in repr(result) and "bearer-secret" not in repr(result)


def test_api_key_enables_live_search(monkeypatch):
    monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("TMDB_API_KEY", "key-secret")
    result = lookup(FILM, live=True, get=lambda *_: (200, response([CANDIDATE]), {}))
    assert result["state"] == "complete_search" and result["requests"] == 1
