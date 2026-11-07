"""Fictional authorization and no-write checks for the Movary watchlist view."""

import json
import sqlite3
import tempfile
import urllib.error
from email.message import Message
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import preferences


def request(user, project, method="GET"):
    result = {}

    def start(status, headers):
        result.update(status=status, headers=dict(headers))

    environ = {
        "HTTP_ORIGIN": preferences.ORIGIN,
        "HTTP_COOKIE": user,
        "REQUEST_METHOD": method,
        "PATH_INFO": "/movary-watchlist/" + project,
        "wsgi.input": BytesIO(),
    }
    result["body"] = json.loads(b"".join(preferences.application(environ, start)))
    return result


def main():
    with tempfile.TemporaryDirectory(dir=".cache/tracker-poc") as name:
        root = Path(name)
        database, sidecar = root / "prefs.sqlite3", root / "watchlist.json"
        with sqlite3.connect(database) as db:
            db.execute(
                "CREATE TABLE preferences (user_id, task_id, interest_score, watchlist, watched_at, personal_notes)"
            )
        own = {
            "version": "tracker-poc-movary-watchlist-v1",
            "source": "Movary",
            "observed_at": "2026-11-06T12:00:00Z",
            "entries": [
                {"tmdb_id": 42, "title": "Fictional film", "added_at": "2026-11-01 09:02:03"}
            ],
        }
        store: dict[str, Any] = {
            "version": "tracker-poc-movary-watchlist-users-v1",
            "project_id": "fictional1",
            "users": {"userA": own},
        }
        sidecar.write_text(json.dumps(store))
        original = sidecar.read_bytes()

        def fake_upstream(path, cookie):
            if cookie == "denied":
                raise urllib.error.HTTPError(path, 403, "forbidden", Message(), None)
            return {"id": "fictional1"}

        with (
            patch.object(preferences, "DATABASE", database),
            patch.object(preferences, "MOVARY_WATCHLIST_SIDECAR", sidecar),
            patch.object(preferences, "current_user", lambda environ: environ["HTTP_COOKIE"]),
            patch.object(preferences, "upstream", fake_upstream),
        ):
            result = request("userA", "fictional1")
            assert result["status"] == "200 OK" and result["body"]["entries"] == own["entries"]
            assert result["headers"]["Cache-Control"] == "no-store"
            assert request("userB", "fictional1")["body"]["status"] == "unknown"
            assert request("userA", "different")["body"]["status"] == "unknown"
            assert request("denied", "fictional1")["status"] == "403 Forbidden"
            assert request("userA", "fictional1", "POST")["status"] == "404 Not Found"
            assert sidecar.read_bytes() == original
            with sqlite3.connect(database) as db:
                assert db.execute("SELECT COUNT(*) FROM preferences").fetchone()[0] == 0
            invalid = json.loads(original)
            invalid["users"]["userA"]["entries"][0]["private_notes"] = "must not leak"
            sidecar.write_text(json.dumps(invalid))
            assert request("userA", "fictional1")["status"] == "503 Service Unavailable"
    print("Fictional Movary watchlist view enforces project/user access and never writes")


if __name__ == "__main__":
    main()
