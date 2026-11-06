"""Exercise independent-key watched refresh using fictional source and tracker data."""

from copy import deepcopy
from unittest.mock import patch

from kaneo_watched_refresh import prepare


def fixtures():
    old_time, new_time = "2026-11-05T12:00:00+00:00", "2026-11-06T12:00:00+00:00"
    event = {"watched": True, "played_watch_dates": [], "history_export_dates": []}
    prior = {
        "source": "Movary",
        "observed_at": old_time,
        "films": {"101": deepcopy(event)},
        "unresolved_history": [],
    }
    sidecar = {
        "version": "tracker-poc-movary-watched-v1",
        "project_id": "fictional-project",
        "users": {"owner": prior, "other": deepcopy(prior)},
    }
    source = {
        "version": "movary-personal-v1",
        "last_successful_refresh": new_time,
        "films": [{"tmdb_id": 101, "watched": True}, {"tmdb_id": 202, "watched": True}],
        "provenance": {
            "api": {
                "played": [
                    {"movie": {"ids": {"tmdb": ident, "movary": ident + 1000}}, "watchDates": []}
                    for ident in (101, 202)
                ],
                "history": [],
                "watchlist": [],
            },
            "history_csv": [],
        },
    }
    return sidecar, source, {"stale": False, "last_successful_refresh": new_time}


def tracker(path):
    if path == "/user/me":
        return {"id": "owner"}
    if path == "/custom-field/project/fictional-project":
        return [{"id": "identity", "name": "POC TMDB ID", "type": "text"}]
    if path == "/custom-field/project/fictional-project/values":
        return [
            {"fieldId": "identity", "value": "101", "taskId": "task-a"},
            {"fieldId": "identity", "value": "202", "taskId": "task-b"},
        ]
    if path in ("/task/task-a", "/task/task-b"):
        return {"id": path.rsplit("/", 1)[1]}
    if path in ("/custom-field/task/task-a", "/custom-field/task/task-b"):
        return [{"fieldId": "identity", "value": "101" if path.endswith("task-a") else "202"}]
    raise AssertionError("Unexpected fictional route")


def run(sidecar, source, status, response=tracker):
    with patch(
        "kaneo_watched_refresh.call", side_effect=lambda _opener, _base, path: response(path)
    ):
        return prepare(None, "http://localhost", "fictional-project", sidecar, source, status)


def main():
    sidecar, source, status = fixtures()
    original = deepcopy((sidecar, source, status))
    result = run(sidecar, source, status)
    assert set(result["users"]["owner"]["films"]) == {"101", "202"}
    assert result["users"]["other"] == sidecar["users"]["other"]
    assert (sidecar, source, status) == original
    for kind in (
        "missing",
        "duplicate",
        "changed",
        "wrong_owner",
        "stale",
        "incomplete",
        "same_time",
    ):
        data, snap, state = deepcopy((sidecar, source, status))

        def response(path, kind=kind):
            result = tracker(path)
            if kind == "missing" and path.endswith("/values"):
                return result[:1]
            if kind == "duplicate" and path.endswith("/values"):
                return [*result, {"fieldId": "identity", "value": "101", "taskId": "task-c"}]
            if kind == "changed" and path.endswith("/task-b") and path.startswith("/custom-field"):
                return [{"fieldId": "identity", "value": "303"}]
            if kind == "wrong_owner" and path == "/user/me":
                return {"id": "someone-else"}
            return result

        if kind == "stale":
            state["stale"] = True
        if kind == "incomplete":
            snap["provenance"]["api"]["history"] = None
        if kind == "same_time":
            snap["last_successful_refresh"] = data["users"]["owner"]["observed_at"]
            state["last_successful_refresh"] = snap["last_successful_refresh"]
        try:
            run(data, snap, state, response)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Fictional {kind} must be rejected")
    print("Fictional bearer-owned watched refresh validates source and project identities")


if __name__ == "__main__":
    main()
