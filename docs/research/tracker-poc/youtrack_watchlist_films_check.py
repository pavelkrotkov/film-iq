"""Fictional neutral issue import: preview, conflicts and uncertain retry."""

import json
from copy import deepcopy
from typing import Any

from movary_watchlist_projection_check import fixtures
from youtrack_client import YouTrackError
from youtrack_watchlist_films import ENDPOINT, apply, neutral_body, plan
from youtrack_watchlist_import import VERSION


def observation():
    snapshot, status = fixtures()
    second = {"ids": {"tmdb": 103, "movary": 503}, "title": "Another fictional film"}
    snapshot["films"].append(
        {"tmdb_id": 103, "movary_id": 503, "title": second["title"], "watchlist": True}
    )
    snapshot["provenance"]["api"]["watchlist"].append({"movie": second, "addedAt": None})
    return snapshot, status


class FakeClient:
    def __init__(self):
        self.rows = [
            {
                "id": "issue-1",
                "idReadable": "FILMREAL-1",
                "project": {"id": "project", "shortName": "FILMREAL"},
                "summary": "Other fictional film",
                "customFields": [
                    {"name": "FilmIQ TMDB ID", "value": 102},
                    {"name": "FilmIQ Lifecycle", "value": {"name": "Discovery"}},
                ],
            }
        ]
        self.posts = []
        self.lost = False
        self.change_after_first = False
        self.watchlist: dict[str, Any] = {
            "status": "available",
            "source": "Movary",
            "observed_at": "2026-11-06T12:34:56+00:00",
            "entries": [
                {"tmdb_id": 101, "title": "Fictional film", "added_at": "2026-11-01 09:02:03"},
                {"tmdb_id": 103, "title": "Another fictional film", "added_at": None},
            ],
        }

    def pages(self, path, *, query):
        if path == "admin/projects":
            return [{"id": "project", "shortName": "FILMREAL"}]
        assert path == "issues" and "FILMREAL" in query["query"]
        return deepcopy(self.rows)

    def request(self, path, *, query=None, body=None):
        if path == "users/me":
            return {"id": "user", "login": "fictional"}
        if path == ENDPOINT + "property-export":
            return {
                "version": VERSION,
                "owner": {"login": "fictional", "ring_id": "ring"},
                "raw": "{}",
            }
        if path == ENDPOINT + "list":
            return deepcopy(self.watchlist)
        if path == "issues":
            assert body is not None and set(body) == {"project", "summary", "customFields"}
            serialized = json.dumps(body).lower()
            assert "watchlist" not in serialized and "watched" not in serialized
            assert "personal_notes" not in serialized and "movary" not in serialized
            issue_id = f"issue-{len(self.rows) + 1}"
            row = {
                "id": issue_id,
                "idReadable": f"FILMREAL-{len(self.rows) + 1}",
                "project": {"id": "project", "shortName": "FILMREAL"},
                "summary": body["summary"],
                "customFields": deepcopy(body["customFields"]),
            }
            self.rows.append(row)
            self.posts.append(body)
            if self.change_after_first:
                self.watchlist["observed_at"] = "2026-11-07T00:00:00+00:00"
            if self.lost:
                self.lost = False
                raise YouTrackError("fictional response lost after creation")
            return {"id": issue_id, "idReadable": row["idReadable"]}
        if path.startswith("issues/"):
            return deepcopy(next(row for row in self.rows if row["id"] == path.split("/")[-1]))
        raise AssertionError("Unexpected fictional request")


def rejects(action):
    try:
        action()
    except (ValueError, RuntimeError):
        return
    raise AssertionError("Expected refusal")


def main():
    snapshot, status = observation()
    client = FakeClient()

    def load():
        return plan(client, snapshot, status, {17, 102}, "source-hash", "status-hash")

    preview = load()
    assert len(preview["pending"]) == 2 and preview["conflicts"] == 0
    assert not client.posts
    assert "watchlist" not in json.dumps(neutral_body(preview["pending"][0], "project")).lower()

    changed = deepcopy(preview)
    changed["snapshot_sha256"] = "changed"
    rejects(lambda: apply(client, changed, load))
    assert not client.posts
    assert apply(client, preview, load) == {"status": "applied", "created": 2}
    assert len(client.rows) == 3 and len(client.posts) == 2
    repeat = load()
    assert not repeat["pending"] and repeat["existing"] == 2
    assert apply(client, repeat, load) == {"status": "applied", "created": 0}

    collision = FakeClient()
    collision.rows[0]["summary"] = " FICTiONAL   film "
    planned = plan(collision, snapshot, status, {17, 102}, "a", "b")
    assert planned["conflicts"] == 1 and len(planned["pending"]) == 1
    rejects(lambda: apply(collision, planned, lambda: planned))
    assert not collision.posts

    denied = FakeClient()
    planned = plan(denied, snapshot, status, {101}, "a", "b")
    assert planned["conflicts"] == 1
    rejects(lambda: apply(denied, planned, lambda: planned))
    assert not denied.posts

    repeated = deepcopy(snapshot)
    repeated["films"][-1]["title"] = " FICTIONAL  FILM "
    repeated["provenance"]["api"]["watchlist"][-1]["movie"]["title"] = " FICTIONAL  FILM "
    same_titles = FakeClient()
    same_titles.watchlist["entries"][-1]["title"] = " FICTIONAL  FILM "
    duplicate_titles = plan(same_titles, repeated, status, {17}, "a", "b")
    assert duplicate_titles["conflicts"] == 1
    rejects(lambda: apply(same_titles, duplicate_titles, lambda: duplicate_titles))
    assert not same_titles.posts

    changed_midrun = FakeClient()

    def load_changed():
        return plan(changed_midrun, snapshot, status, {17}, "a", "b")

    planned = load_changed()
    changed_midrun.change_after_first = True
    rejects(lambda: apply(changed_midrun, planned, load_changed))
    assert len(changed_midrun.posts) == 1, "no second write after changed source view"

    lost = FakeClient()

    def load_lost():
        return plan(lost, snapshot, status, {17}, "a", "b")

    planned = load_lost()
    lost.lost = True
    rejects(lambda: apply(lost, planned, load_lost))
    assert len(lost.posts) == 1 and len(lost.rows) == 2
    assert len(load_lost()["pending"]) == 1, "a fresh preview recognizes the created issue"
    print(
        "Fictional neutral watchlist-film preview, conflicts, idempotence and uncertain write passed"
    )


if __name__ == "__main__":
    main()
