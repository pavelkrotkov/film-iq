"""Check watched mapping without real film or user data."""

from copy import deepcopy
from typing import Any

from youtrack_client import YouTrackError
from youtrack_movary_import import check_same_observation, prepare


def main() -> None:
    def event(day: int) -> dict:
        return {
            "watched": True,
            "played_watch_dates": [{"date": f"2001-01-{day:02}", "plays": 2}],
            "history_export_dates": [None, f"2001-01-{day:02}"],
        }

    observed = "2026-11-05T12:00:00Z"
    sidecar = {
        "users": {
            "fictional": {
                "source": "Movary",
                "observed_at": observed,
                "unresolved_history": [],
                "films": {
                    "101": event(1),
                    "102": event(2),
                    "103": event(2),  # Duplicate source fingerprints are ambiguous.
                    "104": event(3),
                    "107": event(9),
                },
            }
        }
    }
    source = {
        "films": [{"tmdb_id": ident, "watched": True} for ident in (101, 102, 103, 104, 107)],
        "provenance": {"movary_refresh": observed, "movary_refresh_complete": True},
    }
    issues = [
        {
            "idReadable": f"FILMREAL-{number}",
            "customFields": [{"name": "FilmIQ TMDB ID", "value": ident}],
        }
        for number, ident in enumerate((101, 102, 103, 105, 106), start=1)
    ]
    prior_films = {
        "FILMREAL-1": event(1),
        "FILMREAL-2": event(2),
        "FILMREAL-3": event(2),  # Duplicate previous fingerprints are also ambiguous.
        "FILMREAL-4": event(3),  # The unique source ID disagrees with the issue.
        "FILMREAL-5": event(9),  # The unique source ID disagrees with the issue.
    }
    previous: dict[str, Any] = {
        "status": "available",
        "observed_at": observed,
        "films": prior_films,
    }
    original = deepcopy((sidecar, source, issues, previous))
    result = prepare(sidecar, source, issues, previous)
    assert result["version"] == "youtrack-poc-movary-watched-v2"
    assert {key: entry["tmdb_id"] for key, entry in result["films"].items()} == {
        "FILMREAL-1": 101,
        "FILMREAL-2": None,
        "FILMREAL-3": None,
        "FILMREAL-4": None,
        "FILMREAL-5": None,
    }
    assert {
        key: {k: v for k, v in entry.items() if k != "tmdb_id"}
        for key, entry in result["films"].items()
    } == prior_films
    assert (sidecar, source, issues, previous) == original
    check_same_observation(previous, result)
    migrated = {"status": "available", "observed_at": observed, "films": result["films"]}
    assert prepare(sidecar, source, issues, migrated) == result, "migration is repeatable"

    # A one-to-many prior fingerprint cannot borrow a unique source identity.
    duplicate_previous = deepcopy(previous)
    duplicate_previous["films"]["FILMREAL-5"] = event(1)
    try:
        prepare(sidecar, source, issues, duplicate_previous)
    except YouTrackError:
        pass
    else:
        raise AssertionError("Different fingerprint multisets must fail")

    # A contradictory source multiset invalidates every potential binding,
    # even one whose fingerprint appears uniquely on both sides.
    unmatched_previous = deepcopy(previous)
    unmatched_previous["films"]["FILMREAL-5"] = event(8)
    try:
        prepare(sidecar, source, issues, unmatched_previous)
    except YouTrackError:
        pass
    else:
        raise AssertionError("An unmatched fingerprint must stop the entire migration")

    incomplete_sidecar = deepcopy(sidecar)
    del incomplete_sidecar["users"]["fictional"]["unresolved_history"]

    for old in (
        {**previous, "films": {}},
        {**previous, "films": {"FILMREAL-1": {**event(1), "tmdb_id": 123}}},
    ):
        try:
            check_same_observation(old, result)
        except YouTrackError:
            pass
        else:
            raise AssertionError("Changed same-observation data must not be replaced")
    for bad_sidecar, bad_source, bad_issues, bad_previous in (
        (incomplete_sidecar, source, issues, previous),
        (sidecar, source, issues[:-1], previous),
        (
            sidecar,
            {
                **source,
                "provenance": {"movary_refresh": observed, "movary_refresh_complete": False},
            },
            issues,
            previous,
        ),
        (sidecar, source, issues, {**previous, "observed_at": "2026-11-06T12:00:00Z"}),
        (sidecar, source, [*issues, issues[0]], previous),
    ):
        try:
            prepare(bad_sidecar, bad_source, bad_issues, bad_previous)
        except (YouTrackError, ValueError):
            pass
        else:
            raise AssertionError("Incomplete, stale, duplicate or unavailable input must fail")
    print("Synthetic watched migration preserves events and leaves ambiguous identities unknown")


if __name__ == "__main__":
    main()
