"""Exercise the Python refresh importer against the real JS handler, offline."""

import json
import subprocess
from copy import deepcopy
from pathlib import Path

from youtrack_watched_refresh import run

ROOT = Path(__file__).resolve().parents[3]
HARNESS = ROOT / "docs/research/tracker-poc/youtrack-app/tests/watched_refresh_rpc.cjs"


class FictionalClient:
    def __init__(self):
        self.process = subprocess.Popen(
            ["node", str(HARNESS)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        self.writes = 0
        self.lose_response = False

    def rpc(self, message):
        assert self.process.stdin is not None and self.process.stdout is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def request(self, path, *, query=None, body=None):
        if path == "users/me":
            return {"id": "fictional-user", "login": "admin"}
        prefix = "extensionEndpoints/filmiq-poc/movary/"
        if not path.startswith(prefix):
            raise AssertionError("Unexpected fixture request")
        method = "GET" if body is None else "POST"
        if body is not None:
            self.writes += 1
        result = self.rpc(
            {"method": method, "path": "/" + path[len(prefix) :], "query": query, "body": body}
        )
        if body is not None and self.lose_response:
            self.lose_response = False
            raise TimeoutError("Fictional response lost")
        if result.get("status") != 200:
            raise ValueError("Fictional handler rejected request")
        return result["value"]

    def pages(self, path, *, query):
        assert path == "issues" and query["query"].startswith("project: {FILMREAL}")
        return [
            {
                "idReadable": f"FILMREAL-{number}",
                "customFields": [{"name": "FilmIQ TMDB ID", "value": ident}],
            }
            for number, ident in ((1, 101), (2, 202))
        ]

    def close(self):
        assert self.process.stdin is not None and self.process.stdout is not None
        self.process.stdin.close()
        self.process.wait(timeout=5)
        self.process.stdout.close()


def source(stamp):
    records = [(101, "2001-01-03"), (202, "2001-01-02")]
    snapshot = {
        "version": "movary-personal-v1",
        "last_successful_refresh": stamp,
        "films": [{"tmdb_id": ident, "watched": True} for ident, _ in records],
        "provenance": {
            "api": {
                "played": [
                    {
                        "movie": {"ids": {"tmdb": ident, "movary": ident + 1000}},
                        "watchDates": [{"date": day, "plays": 2}],
                    }
                    for ident, day in records
                ],
                "history": [],
                "watchlist": [],
            },
            "history_csv": [],
        },
    }
    return snapshot, {"stale": False, "last_successful_refresh": stamp}


def main() -> None:
    client = FictionalClient()
    try:
        snapshot, status = source("2026-11-06T12:00:00+00:00")
        originals = deepcopy((snapshot, status))
        before = client.rpc({"action": "raw"})["raw"]
        assert run(client, snapshot, status) == {"status": "preview", "films": 2, "historical": 1}
        assert client.writes == 0 and client.rpc({"action": "raw"})["raw"] == before
        assert run(client, snapshot, status, apply=True) == {
            "status": "imported",
            "films": 2,
            "historical": 1,
        }
        saved = client.rpc({"action": "raw"})["raw"]
        assert run(client, snapshot, status, apply=True) == {
            "status": "unchanged",
            "films": 2,
            "historical": 1,
        }
        assert client.rpc({"action": "raw"})["raw"] == saved
        assert (snapshot, status) == originals

        bad_snapshot = deepcopy(snapshot)
        bad_snapshot["provenance"]["api"]["history"].append(
            {"movie": {"ids": {"tmdb": 303, "movary": 1303}}}
        )
        try:
            run(client, bad_snapshot, status, apply=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Incomplete source was accepted")
        assert client.rpc({"action": "raw"})["raw"] == saved

        later, later_status = source("2026-11-07T12:00:00+00:00")
        client.rpc({"action": "hidden", "value": True})
        try:
            run(client, later, later_status, apply=True)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Inaccessible stored history was replaced")
        assert client.rpc({"action": "raw"})["raw"] == saved
    finally:
        client.close()
    client = FictionalClient()
    try:
        snapshot, status = source("2026-11-06T12:00:00+00:00")
        client.lose_response = True
        try:
            run(client, snapshot, status, apply=True)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Lost response must remain unconfirmed")
        saved = client.rpc({"action": "raw"})["raw"]
        assert run(client, snapshot, status, apply=True) == {
            "status": "unchanged",
            "films": 2,
            "historical": 1,
        }
        assert client.rpc({"action": "raw"})["raw"] == saved
    finally:
        client.close()
    print("Fictional Python importer and JS handler preserve watched history, retries and access")


if __name__ == "__main__":
    main()
