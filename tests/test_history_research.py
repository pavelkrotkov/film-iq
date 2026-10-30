"""Search completeness never establishes film identity or catalog absence."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from docs.research.history.lookup import lookup

FILM = {"key": "test", "query": "A Film"}
CANDIDATE = {
    "id": 1,
    "title": "A Film",
    "original_title": "Un Film",
    "release_date": "2011-01-01",
    "original_language": "fr",
}


def response(rows, page=1, total_pages=1, total_results=None):
    return json.dumps(
        {
            "page": page,
            "total_pages": total_pages,
            "total_results": len(rows) if total_results is None else total_results,
            "results": rows,
        }
    ).encode()


def run(monkeypatch, body, status=200, **kwargs):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "test-token")
    return lookup(FILM, live=True, get=lambda *_: (status, body, {}), **kwargs)


def test_dry_run_and_sample(monkeypatch):
    monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
    sample = json.loads(Path("docs/research/history/sample.json").read_text())
    assert len(sample) == 14 and all(row["accepted_tmdb_id"] is None for row in sample)
    assert all(lookup(row, live=True)["requests"] == 0 for row in sample)


@pytest.mark.parametrize(
    "body,status,phase",
    [
        (b"", 429, "http_status"),
        (b'{"results":', 200, "json_decode"),
        (response([CANDIDATE], total_results=2), 200, "result_set"),
        (response([CANDIDATE, CANDIDATE]), 200, "result_set"),
        (response([CANDIDATE], total_pages=10), 200, "page_budget"),
        (response([CANDIDATE | {"id": True}]), 200, "schema"),
    ],
)
def test_failed_partial_and_truncated_remain_unknown(monkeypatch, body, status, phase):
    result = run(monkeypatch, body, status)
    assert result["state"] == "unknown" and not result["confirmed_absent"]
    assert result["identity"] == "unreviewed" and "candidates" not in result
    assert result["requests"] == 1
    assert result["failure"]["phase"] == phase
    if phase == "page_budget":
        assert result["attempts"][0]["total_pages"] == 10


def test_empty_search_is_not_confirmed_absence(monkeypatch):
    result = run(monkeypatch, response([], total_pages=0))
    # An empty query can reflect alternate spellings or catalog search behavior.
    assert result["state"] == "complete_search" and result["candidates"] == []
    assert not result["confirmed_absent"] and result["identity"] == "unreviewed"
