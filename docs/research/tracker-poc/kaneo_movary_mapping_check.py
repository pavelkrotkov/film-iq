"""Check synthetic per-user source isolation and repeated/unknown watch dates."""

from copy import deepcopy
from typing import Any

from kaneo_movary_mapping import mapping, merge


def main() -> None:
    stamp = "2026-11-05T12:00:00+00:00"
    snapshot: dict[str, Any] = {
        "version": "movary-personal-v1",
        "last_successful_refresh": stamp,
        "films": [{"tmdb_id": 123, "watched": True}],
        "provenance": {
            "api": {
                "played": [
                    {
                        "movie": {"ids": {"tmdb": 123}},
                        "watchDates": [
                            {"date": None, "plays": 2, "comment": "never copy"},
                            {"date": "2020-01-02", "plays": 1},
                        ],
                    }
                ]
            },
            "history_csv": [
                {"tmdbId": "123", "watchedAt": "2020-01-02", "comment": "never copy"},
                {"tmdbId": "123", "watchedAt": "2020-01-02"},
                {"tmdbId": "123", "watchedAt": ""},
            ],
        },
    }
    status = {"stale": False, "last_successful_refresh": stamp}
    observation = mapping(snapshot, status)
    film = observation["films"]["123"]
    assert film["played_watch_dates"] == [
        {"date": None, "plays": 2},
        {"date": "2020-01-02", "plays": 1},
    ]
    assert film["history_export_dates"] == ["2020-01-02", "2020-01-02", None]
    assert "comment" not in str(observation)
    a = merge(None, "project", "user-a", observation)
    b = merge(a, "project", "user-b", {"source": "Movary", "films": {}})
    assert b["users"]["user-a"] == observation and b["users"]["user-b"]["films"] == {}
    assert merge(b, "project", "user-a", observation) == b
    bad_status = dict(status, stale=True)
    bad_snapshot = deepcopy(snapshot)
    bad_snapshot["provenance"]["api"]["played"][0]["watchDates"][0]["plays"] = 0
    for current, state in ((snapshot, bad_status), (bad_snapshot, status)):
        try:
            mapping(current, state)
        except ValueError:
            pass
        else:
            raise AssertionError("stale or malformed history must fail")
    try:
        merge(b, "different-project", "user-a", observation)
    except ValueError:
        pass
    else:
        raise AssertionError("cross-project replacement must fail")
    print("Synthetic source-tagged watched mapping checks passed")


if __name__ == "__main__":
    main()
