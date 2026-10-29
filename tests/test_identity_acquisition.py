"""Acquisition checks stay offline and exercise real failure/completeness rules."""

import http.client
import json
import urllib.error
from contextlib import nullcontext
from datetime import datetime
from email.message import Message
from pathlib import Path
from unittest.mock import Mock

import pytest

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


def test_missing_entities_fail_retrieval(monkeypatch) -> None:
    """A missing entity response cannot justify excluding that search result."""
    monkeypatch.setattr(acquisition, "get", lambda parameters: ("test-only", {"entities": {}}))
    with pytest.raises(ValueError, match="Incomplete entity"):
        acquisition.entities(["Q1"])


def test_frozen_candidates_rebuild_from_cc0_evidence() -> None:
    """Candidate construction is reproducible independently of observations.

    Rebuild every retained lead from its CC0 claims, labels and director records.
    """
    path = Path(__file__).parent / "fixtures" / "identity" / "specialty-candidates.json"
    snapshot = json.loads(path.read_text())
    for record in snapshot["cases"][:4]:
        retrieval = record["retrieval"]
        movies = retrieval["candidate_evidence"]
        people = retrieval["director_evidence"]
        assert acquisition.candidates(movies, people) == record["candidates"]


def returned_search_ids(retrieval) -> list[str]:
    """Recover the original search membership from retained API pages."""
    return list(
        dict.fromkeys(
            item["id"] for page in retrieval["pages"] for item in page["response"]["search"]
        )
    )


@pytest.mark.parametrize("case_index", range(4))
def test_returned_entity_partition_replays_offline(case_index) -> None:
    """Replay membership from claims, including exclusions, without live queries.

    Search IDs alone do not establish whether an entity had a usable movie ID.
    The union must cover the entire search, with neither gaps nor overlap.
    """
    path = Path(__file__).parent / "fixtures" / "identity" / "specialty-candidates.json"
    retrieval = json.loads(path.read_text())["cases"][case_index]["retrieval"]
    retained = retrieval["candidate_evidence"]
    excluded = retrieval["excluded_evidence"]
    evidence = retained | excluded
    assert not retained.keys() & excluded.keys()
    assert retrieval["returned_entities"] == returned_search_ids(retrieval)
    assert evidence.keys() == set(returned_search_ids(retrieval))
    partition = {key for key, entity in evidence.items() if acquisition.values(entity, "P4947")}
    assert partition == retained.keys()
    assert evidence.keys() - partition == set(retrieval["excluded_without_P4947"])


def test_reconciled_exclusions_use_unchanged_revisions() -> None:
    """Later reconciliation must not masquerade as original acquisition.

    The public latest-revision timestamps predate acquisition, establishing that
    these same revisions were current then. Only the exclusion property is kept.
    """
    path = Path(__file__).parent / "fixtures" / "identity" / "specialty-candidates.json"
    snapshot = json.loads(path.read_text())
    for record in snapshot["cases"][:4]:
        for entity in record["retrieval"]["excluded_evidence"].values():
            assert entity["revision"] > 0
            assert datetime.fromisoformat(entity["modified"]) <= datetime.fromisoformat(
                record["retrieval"]["observed_at"]
            )
            assert entity["claims"].keys() == {"P4947"}


@pytest.mark.parametrize(
    "statements", [[], [{"rank": "deprecated", "mainsnak": {"datavalue": {"value": "999"}}}]]
)
def test_collect_retains_minimal_exclusion_claims(monkeypatch, statements) -> None:
    """Retain absent or deprecated P4947 evidence before requesting directors.

    Unrelated claims and labels are unnecessary to audit exclusion membership;
    keep only the revision and the exact P4947 statements, never inferred truth.
    """
    entity = {
        "lastrevid": 42,
        "claims": {"P4947": statements, "P31": ["unused"]},
        "labels": {"en": "unused"},
    }
    monkeypatch.setattr(acquisition, "search", lambda title, retrieval: ["Q1"])
    monkeypatch.setattr(acquisition, "entities", lambda ids: dict.fromkeys(ids, entity))
    retrieval = {}
    assert acquisition.collect("Synthetic", retrieval) == []
    assert retrieval["excluded_without_P4947"] == ["Q1"]
    assert retrieval["excluded_evidence"] == {
        "Q1": {"revision": 42, "claims": {"P4947": statements}}
    }


def assert_recorded_failure(record, error) -> None:
    """Transport failures leave an attempted record, not negative film evidence."""
    assert record["retrieval"]["complete"] is False
    assert record["retrieval"]["error"] == f"{type(error).__name__}: {error}"
    assert record["truth"]["tmdb_id"] is None
    assert record["candidates"] == []


@pytest.mark.parametrize(
    "error",
    [
        http.client.IncompleteRead(b'{"search":', 10),
        http.client.RemoteDisconnected("body disconnected"),
    ],
)
def test_response_body_failure_keeps_attempted_cohort(monkeypatch, tmp_path, error) -> None:
    """Exercise real get/json.load through main, including its saved output.

    A truncated or disconnected body must not abort the cohort before appending
    the attempted case. A second case proves acquisition continues without retry.
    """
    body = Mock(read=Mock(side_effect=error))
    monkeypatch.setattr(
        acquisition.urllib.request, "urlopen", lambda request, timeout: nullcontext(body)
    )
    monkeypatch.setattr(acquisition.time, "sleep", lambda seconds: None)
    source, destination = tmp_path / "observations.json", tmp_path / "candidates.json"
    cases = [
        {"id": name, "observation": {"title": "Synthetic"}, "source": {"url": "test-only"}}
        for name in ("first", "second")
    ]
    source.write_text(json.dumps({"version": "synthetic", "cases": cases}))
    monkeypatch.setattr(acquisition.sys, "argv", ["acquire", str(source), str(destination)])
    acquisition.main()
    records = json.loads(destination.read_text())["cases"]
    assert [record["id"] for record in records] == ["first", "second"]
    for record in records:
        assert_recorded_failure(record, error)
    assert body.read.call_count == 2
