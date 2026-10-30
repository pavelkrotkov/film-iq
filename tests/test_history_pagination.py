"""Multi-page and transport evidence remains unknown on incomplete acquisition."""

import pytest
from test_history_research import CANDIDATE, FILM, lookup, response


@pytest.mark.parametrize("outcome", ["complete", "http", "changed_counts"])
def test_paginated_evidence(monkeypatch, outcome):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "test-token")

    def get(query, page, token):
        total = 3 if page == 2 and outcome == "changed_counts" else 2
        status = 503 if page == 2 and outcome == "http" else 200
        return status, response([CANDIDATE | {"id": page}], page, total, total), {}

    result = lookup(FILM, True, get=get)
    assert result["requests"] == 2
    assert result["attempts"][0]["candidates"] == [CANDIDATE]
    if outcome == "complete":
        assert [row["id"] for row in result["candidates"]] == [1, 2]
    else:
        assert result["state"] == "unknown" and "candidates" not in result


def test_transport_failure_preserves_attempt(monkeypatch):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "test-token")

    def get(*_):
        raise TimeoutError("test-token")

    result = lookup(FILM, True, get=get)
    assert result["state"] == "unknown" and result["requests"] == 1
    assert result["failure"] == {"phase": "transport", "type": "TimeoutError"}
    assert "test-token" not in repr(result)
