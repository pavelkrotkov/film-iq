"""Fictional watchlist importer: private backup, readback and project scope."""

import json
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import youtrack_watched_property_backup as backup
from movary_watchlist_projection_check import fixtures
from youtrack_watchlist_import import ENDPOINT, VERSION, run
from youtrack_watchlist_recovery import export, restore


class FakeClient:
    def __init__(self):
        self.owner = {"login": "fictional", "ring_id": "fictional-ring"}
        self.raw = json.dumps(
            {
                "version": "youtrack-poc-movary-watchlists-v1",
                "projects": {
                    "FILMPOC": {
                        "version": "tracker-poc-movary-watchlist-v1",
                        "source": "Movary",
                        "project": "FILMPOC",
                        "observed_at": "2026-11-05T12:00:00+00:00",
                        "entries": [],
                    }
                },
            }
        )
        self.posts = 0

    def pages(self, path, *, query):
        assert path == "issues" and "FILMREAL" in query["query"]
        return [
            {
                "id": "fictional-issue",
                "idReadable": "FILMREAL-1",
                "project": {"shortName": "FILMREAL"},
                "customFields": [{"name": "FilmIQ TMDB ID", "value": 102}],
            }
        ]

    def request(self, path, *, query=None, body=None):
        if path == "users/me":
            return {"id": "fictional-user", "login": "fictional"}
        if path == ENDPOINT + "property-export":
            return {"version": VERSION, "owner": deepcopy(self.owner), "raw": self.raw}
        if path == ENDPOINT + "import":
            assert body is not None
            assert body["owner"] == self.owner and body["expected"] == self.raw
            state = json.loads(self.raw)
            state["projects"][body["snapshot"]["project"]] = deepcopy(body["snapshot"])
            self.raw = json.dumps(state)
            self.posts += 1
            return {"status": "imported", "entries": len(body["snapshot"]["entries"])}
        if path == ENDPOINT + "list":
            assert query is not None
            saved = json.loads(self.raw)["projects"][query["project"]]
            return {
                "status": "available",
                "source": "Movary",
                "observed_at": saved["observed_at"],
                "entries": saved["entries"],
            }
        if path == ENDPOINT + "property-restore":
            assert body is not None
            assert body["expected"]["raw"] == self.raw
            assert body["backup"]["owner"] == self.owner
            self.raw = body["backup"]["raw"]
            self.posts += 1
            return {"status": "restored"}
        raise AssertionError(f"Unexpected fictional request: {path}")


def main() -> None:
    base = Path(__file__).resolve().parents[3] / ".cache/tracker-poc"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fictional-youtrack-watchlist-", dir=base) as directory:
        root = Path(directory)
        root.chmod(0o700)
        snapshot, status = fixtures()
        client = FakeClient()
        before = deepcopy(client.raw)
        preview = run(client, snapshot, status, "FILMREAL")
        assert preview == {"status": "preview", "entries": 1, "missing_films": 1}
        assert client.raw == before and client.posts == 0
        with patch.object(backup, "PROJECT", root):
            target = root / "before.json"
            result = run(client, snapshot, status, "FILMREAL", apply=True, backup=target)
            assert result == {"status": "imported", "entries": 1, "missing_films": 1}
            saved = json.loads(target.read_text())
            assert target.stat().st_mode & 0o777 == 0o600 and saved["raw"] == before
            state = json.loads(client.raw)
            assert state["projects"]["FILMPOC"] == json.loads(before)["projects"]["FILMPOC"]
            entry = state["projects"]["FILMREAL"]["entries"][0]
            assert entry == {
                "tmdb_id": 101,
                "title": "Fictional film",
                "added_at": "2026-11-01 09:02:03",
            }
            assert "personal_enjoyment" not in client.raw and "watched_dates" not in client.raw
            assert client.posts == 1
            expected = root / "current.json"
            export(client, expected)
            assert restore(client, target, expected) == "preview"
            assert client.posts == 1
            assert restore(client, target, expected, apply=True) == "restored"
            assert client.raw == before and client.posts == 2
            try:
                restore(client, target, expected, apply=True)
            except ValueError:
                pass
            else:
                raise AssertionError("Stale expected property was accepted")
            try:
                run(client, snapshot, status, "FILMREAL", apply=True, backup=target)
            except FileExistsError:
                pass
            else:
                raise AssertionError("An existing backup was overwritten")
            assert client.posts == 2
    print("Fictional YouTrack watchlist import preserves owner, other project and private backup")


if __name__ == "__main__":
    main()
