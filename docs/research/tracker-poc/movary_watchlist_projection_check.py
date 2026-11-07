"""Fictional check of read-only Movary watchlist planning."""

from copy import deepcopy

from movary_watchlist_projection import project


def fixtures():
    movie = {"ids": {"tmdb": 101, "movary": 501}, "title": "Fictional film"}
    snapshot = {
        "version": "movary-personal-v1",
        "last_successful_refresh": "2026-11-06T12:34:56+00:00",
        "films": [
            {
                "tmdb_id": 101,
                "movary_id": 501,
                "title": "Fictional film",
                "watchlist": True,
                "personal_enjoyment": 9,
                "watched_dates": ["2020-01-01"],
            },
            {"tmdb_id": 102, "movary_id": 502, "title": "Other", "watchlist": False},
        ],
        "provenance": {
            "api": {
                "played": [],
                "history": [],
                "watchlist": [{"movie": movie, "addedAt": "2026-11-01 09:02:03"}],
            }
        },
    }
    return snapshot, {
        "stale": False,
        "last_successful_refresh": snapshot["last_successful_refresh"],
    }


def fails(snapshot, status, existing):
    try:
        project(snapshot, status, existing)
    except ValueError:
        return
    raise AssertionError("An invalid input was accepted")


def main():
    snapshot, status = fixtures()
    before = deepcopy((snapshot, status))
    result = project(snapshot, status, [102])
    assert result == {
        "version": "tracker-poc-movary-watchlist-v1",
        "source": "Movary",
        "observed_at": "2026-11-06T12:34:56+00:00",
        "entries": [{"tmdb_id": 101, "title": "Fictional film", "added_at": "2026-11-01 09:02:03"}],
        "missing_film_ids": [101],
    }
    assert project(snapshot, status, [101, 102])["missing_film_ids"] == []
    assert (snapshot, status) == before
    assert "personal_enjoyment" not in str(result) and "watched_dates" not in str(result)

    disagrees = deepcopy(snapshot)
    disagrees["films"][0]["title"] = "Different fictional title"
    assert project(disagrees, status, [102])["entries"][0]["title"] is None
    unknown_date = deepcopy(snapshot)
    unknown_date["provenance"]["api"]["watchlist"][0]["addedAt"] = None
    assert project(unknown_date, status, [102])["entries"][0]["added_at"] is None

    for mutation in (
        "duplicate",
        "missing_collection",
        "flag_mismatch",
        "crosswalk",
        "date",
        "naive_observation",
    ):
        bad = deepcopy(snapshot)
        rows = bad["provenance"]["api"]["watchlist"]
        if mutation == "duplicate":
            rows.append(deepcopy(rows[0]))
        elif mutation == "missing_collection":
            del bad["provenance"]["api"]["watchlist"]
        elif mutation == "flag_mismatch":
            bad["films"][0]["watchlist"] = False
        elif mutation == "crosswalk":
            bad["films"][0]["movary_id"] = 999
        elif mutation == "date":
            rows[0]["addedAt"] = "2026-02-30 12:00:00"
        else:
            bad["last_successful_refresh"] = "2026-11-06T12:34:56"
        marker = {**status, "last_successful_refresh": bad["last_successful_refresh"]}
        fails(bad, marker, [102])
    fails(snapshot, {**status, "stale": True}, [102])
    fails(snapshot, {**status, "last_successful_refresh": "different"}, [102])
    fails(snapshot, status, [102, 102])
    print(
        "Fictional watchlist projection preserves source precision and rejects incomplete identities"
    )


if __name__ == "__main__":
    main()
