"""Check watched mapping without real film or user data."""

from youtrack_movary_import import prepare


def main() -> None:
    event = {
        "watched": True,
        "played_watch_dates": [{"date": None, "plays": 2}],
        "history_export_dates": [None],
    }
    sidecar = {
        "users": {
            "fictional": {
                "source": "Movary",
                "observed_at": "2026-11-05T12:00:00Z",
                "unresolved_history": [],
                "films": {"987654321": event},
            }
        }
    }
    source = {"films": [{"tmdb_id": 987654321, "watched": True}]}
    issue = {
        "idReadable": "FILMREAL-1",
        "customFields": [{"name": "FilmIQ TMDB ID", "value": 987654321}],
    }
    result = prepare(sidecar, source, [issue])
    assert result["films"] == {"FILMREAL-1": event}
    try:
        prepare(sidecar, source, [])
    except ValueError:
        raise AssertionError("Expected a missing-issue error") from None
    except RuntimeError:
        pass
    else:
        raise AssertionError("An incomplete mapping must be rejected")
    source["films"].append({"tmdb_id": 123456789, "watched": True})
    try:
        prepare(sidecar, source, [issue])
    except ValueError:
        pass
    else:
        raise AssertionError("A partial source snapshot must be rejected")
    print("Synthetic YouTrack watched mapping checks passed")


if __name__ == "__main__":
    main()
