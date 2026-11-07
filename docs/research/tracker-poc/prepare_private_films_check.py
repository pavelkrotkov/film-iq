"""Deterministic check for the private, read-only POC handoff."""

from copy import deepcopy
from typing import Any

from prepare_private_films import prepare


def main() -> None:
    timestamp = "2026-11-05T12:00:00+00:00"
    snapshot = {
        "version": "movary-personal-v1",
        "last_successful_refresh": timestamp,
        "films": [
            {
                "tmdb_id": 2,
                "title": "A fictional watched film",
                "watched": True,
                "watched_dates": [None],
                "personal_enjoyment": 9,
                "watchlist": True,
            }
        ],
        "unresolved": {"history": [], "ratings": []},
    }
    status = {"stale": False, "last_successful_refresh": timestamp}
    report: dict[str, Any] = {
        "last_successful_refresh": timestamp,
        "personal_state_stale": False,
        "completeness": "intentionally_partial",
        "suggested_unwatched": [
            {
                "tmdb_id": 1,
                "raw_title": "A fictional candidate",
                "watched": False,
                "identity_status": "reviewed",
                "extraction_status": "accepted",
                "source_reasons": [{"source_url": "https://example.org/ballot"}],
                "display": {"title": "Unlicensed catalog copy"},
            }
        ],
    }
    output = prepare(snapshot, status, report)
    assert [film["tmdb_id"] for film in output["films"]] == [1, 2]
    assert output["films"][1]["watched_dates"] == [None]
    assert "personal_enjoyment" not in output["films"][1]
    assert "watchlist" not in output["films"][1]
    assert "display" not in output["films"][0]
    stale = dict(status, stale=True)
    duplicate = deepcopy(report)
    duplicate["suggested_unwatched"].append(duplicate["suggested_unwatched"][0])
    for bad_status, bad_report in ((stale, report), (status, duplicate)):
        try:
            prepare(snapshot, bad_status, bad_report)
        except ValueError:
            pass
        else:
            raise AssertionError("Stale or duplicate inputs must fail")
    print("Private handoff checks passed")


if __name__ == "__main__":
    main()
