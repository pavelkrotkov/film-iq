"""Offline fictional checks for a newer watched-observation proposal."""

from copy import deepcopy
from typing import Any

from youtrack_watched_refresh_proposal import propose


def event(ident, day):
    return {
        "watched": True,
        "tmdb_id": ident,
        "played_watch_dates": [{"date": f"2001-01-{day:02}", "plays": 2}],
        "history_export_dates": [],
    }


def issue(number, ident):
    return {
        "idReadable": f"FILMREAL-{number}",
        "customFields": [{"name": "FilmIQ TMDB ID", "value": ident}],
    }


def main() -> None:
    old_time = "2026-11-05T12:00:00+00:00"
    new_time = "2026-11-06T12:00:00+00:00"
    prior: dict[str, Any] = {
        "status": "available",
        "source": "Movary",
        "observed_at": old_time,
        "films": {
            "FILMREAL-1": event(None, 1),
            "FILMREAL-2": event(202, 2),
            "FILMREAL-4": event(404, 4),
            "FILMREAL-5": event(505, 5),
        },
    }
    issues = [issue(1, 101), issue(2, 303), issue(3, 202), issue(4, 404), issue(5, 505)]
    watched = {101: 6, 202: 2, 303: 3, 404: 4}
    snapshot: dict[str, Any] = {
        "version": "movary-personal-v1",
        "last_successful_refresh": new_time,
        "films": [{"tmdb_id": ident, "watched": True} for ident in watched],
        "provenance": {
            "api": {
                "played": [
                    {
                        "movie": {"ids": {"tmdb": ident, "movary": ident + 1000}},
                        "watchDates": [{"date": f"2001-01-{day:02}", "plays": 2}],
                    }
                    for ident, day in watched.items()
                ],
                "history": [],
                "watchlist": [],
            },
            "history_csv": [],
        },
    }
    status = {"stale": False, "last_successful_refresh": new_time}
    inputs = deepcopy((snapshot, status, issues, prior))
    proposal = propose(snapshot, status, issues, prior)
    assert proposal["observed_at"] == new_time
    assert {key: film["tmdb_id"] for key, film in proposal["films"].items()} == {
        "FILMREAL-1": 101,
        "FILMREAL-2": 303,
        "FILMREAL-3": 202,
        "FILMREAL-4": 404,
    }
    history = {item["issue_id"]: item for item in proposal["historical"]}
    assert set(history) == {"FILMREAL-1", "FILMREAL-2", "FILMREAL-5"}
    assert history["FILMREAL-1"] == {
        "issue_id": "FILMREAL-1",
        "observed_at": old_time,
        "reason": "unbound",
        "film": event(None, 1),
    }
    assert history["FILMREAL-2"]["film"] == event(202, 2)
    assert history["FILMREAL-2"]["observed_at"] == old_time
    assert history["FILMREAL-5"]["reason"] == "superseded"
    assert (snapshot, status, issues, prior) == inputs

    later = deepcopy(snapshot)
    later["last_successful_refresh"] = "2026-11-07T12:00:00+00:00"
    again = propose(
        later,
        {"stale": False, "last_successful_refresh": later["last_successful_refresh"]},
        issues,
        proposal,
    )
    assert again["historical"] == proposal["historical"]

    history_only = deepcopy(snapshot)
    history_only["films"].extend(
        [{"tmdb_id": 606, "watched": True}, {"tmdb_id": 707, "watched": True}]
    )
    history_only["provenance"]["api"]["history"].append(
        {"movie": {"ids": {"tmdb": 606, "movary": 1606}}}
    )
    history_only["provenance"]["history_csv"].append({"tmdbId": "707", "watchedAt": "2001-01-07"})
    expanded = propose(history_only, status, [*issues, issue(6, 606), issue(7, 707)], prior)
    assert expanded["films"]["FILMREAL-6"]["played_watch_dates"] == []
    assert expanded["films"]["FILMREAL-6"]["history_export_dates"] == []
    assert expanded["films"]["FILMREAL-7"]["history_export_dates"] == ["2001-01-07"]

    missing_collection = deepcopy(snapshot)
    del missing_collection["provenance"]["api"]["history"]
    unresolved = deepcopy(snapshot)
    unresolved["provenance"]["history_csv"] = [
        {"tmdbId": "", "watchedAt": "2001-01-01", "title": "Fictional"}
    ]
    duplicate = [*issues, issue(6, 101)]
    missing = [item for item in issues if item["idReadable"] != "FILMREAL-3"]
    invalid_history = deepcopy(prior)
    invalid_history["films"]["FILMREAL-1"]["history_export_dates"] = ["2001-02-30"]
    invalid_source_date = deepcopy(snapshot)
    invalid_source_date["provenance"]["api"]["played"][0]["watchDates"][0]["date"] = "20010101"
    omitted_api_history = deepcopy(snapshot)
    omitted_api_history["provenance"]["api"]["history"].append(
        {"movie": {"ids": {"tmdb": 606, "movary": 1606}}}
    )
    invented_watch = deepcopy(snapshot)
    invented_watch["films"].append({"tmdb_id": 606, "watched": True})
    noncanonical_issue = deepcopy(issues)
    noncanonical_issue[0]["idReadable"] = "FILMREAL-01"
    for args in (
        (snapshot, {"stale": True, "last_successful_refresh": new_time}, issues, prior),
        (missing_collection, status, issues, prior),
        (unresolved, status, issues, prior),
        (snapshot, status, duplicate, prior),
        (snapshot, status, missing, prior),
        (snapshot, status, issues, invalid_history),
        (invalid_source_date, status, issues, prior),
        (omitted_api_history, status, issues, prior),
        (invented_watch, status, issues, prior),
        (snapshot, status, noncanonical_issue, prior),
        (snapshot, status, issues, {**prior, "observed_at": new_time}),
    ):
        try:
            propose(*args)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError("Invalid or incomplete refresh was accepted")
    assert (snapshot, status, issues, prior) == inputs
    print("Fictional newer refresh proposal preserves timestamped unknown and corrected history")


if __name__ == "__main__":
    main()
