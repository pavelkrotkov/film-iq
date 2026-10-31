"""Acquisition checks stay offline and exercise real failure/completeness rules."""

import urllib.error
from email.message import Message

from film_iq.identity import wikidata_sample as acquisition


def test_rate_limit_is_incomplete_not_negative(monkeypatch) -> None:
    """A failed request supplies no absence evidence.

    An empty tuple after HTTP 429 must retain its retrieval failure status.
    """

    def limited(parameters):
        raise urllib.error.HTTPError(
            acquisition.ENDPOINT, 429, "Too Many Requests", Message(), None
        )

    monkeypatch.setattr(acquisition, "get", limited)
    record = acquisition.acquire(
        {"id": "test", "observation": {"title": "Synthetic"}, "source": {"url": "test-only"}}
    )
    assert record["retrieval"]["complete"] is False
    assert "429" in record["retrieval"]["error"]
    assert record["truth"]["tmdb_id"] is None
    assert record["candidates"] == []


def test_search_follows_continuation_and_marks_cap(monkeypatch) -> None:
    """Follow every page, but keep a capped search explicitly incomplete.

    This prevents silently measuring only the first page of a broad query.
    """
    pages = iter([{"search": [{"id": "Q1"}], "search-continue": 50}, {"search": [{"id": "Q2"}]}])
    monkeypatch.setattr(acquisition, "get", lambda parameters: ("test-only", next(pages)))
    retrieval = {"pages": [], "search_complete": False}
    assert acquisition.search("Synthetic", retrieval) == ["Q1", "Q2"]
    assert retrieval["search_complete"] is True
    monkeypatch.setattr(
        acquisition, "get", lambda parameters: ("test-only", {"search": [], "search-continue": 50})
    )
    retrieval = {"pages": [], "search_complete": False}
    assert acquisition.search("Synthetic", retrieval) == []
    assert retrieval["search_complete"] is False
    assert len(retrieval["pages"]) == 10


def returned_search_ids(retrieval) -> list[str]:
    """Recover the original search membership from retained API pages."""
    return list(
        dict.fromkeys(
            item["id"] for page in retrieval["pages"] for item in page["response"]["search"]
        )
    )


def assert_recorded_failure(record, error) -> None:
    """Transport failures leave an attempted record, not negative film evidence."""
    assert record["retrieval"]["complete"] is False
    assert record["retrieval"]["error"] == f"{type(error).__name__}: {error}"
    assert record["truth"]["tmdb_id"] is None
    assert record["candidates"] == []
