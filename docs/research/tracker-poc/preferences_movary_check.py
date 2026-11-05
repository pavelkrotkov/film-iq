"""Verify a fictional per-user Movary sidecar stays private and read-only."""

import json
import sqlite3
import tempfile
import urllib.error
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import preferences


def request(user: str, project: str):
    result = {}

    def start(status, headers):
        result.update(status=status, headers=dict(headers))

    environ = {
        "HTTP_ORIGIN": preferences.ORIGIN,
        "HTTP_COOKIE": user,
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/movary/" + project,
        "wsgi.input": BytesIO(),
    }
    result["body"] = json.loads(b"".join(preferences.application(environ, start)))
    return result


def check():
    with tempfile.TemporaryDirectory(dir=".cache/tracker-poc") as name:
        root = Path(name)
        preferences.DATABASE = root / "prefs.sqlite3"
        preferences.MOVARY_SIDECAR = root / "watched.json"
        with sqlite3.connect(preferences.DATABASE) as db:
            db.execute(
                "CREATE TABLE preferences (user_id, task_id, interest_score, watchlist, watched_at, personal_notes)"
            )
        preferences.MOVARY_SIDECAR.write_text(
            json.dumps(
                {
                    "version": "tracker-poc-movary-watched-v1",
                    "project_id": "synthetic1",
                    "users": {
                        "userA": {
                            "source": "Movary",
                            "observed_at": "2026-11-05T00:00:00Z",
                            "films": {"12": {"watched": True}},
                        }
                    },
                }
            )
        )

        def fake_upstream(path, cookie):
            if cookie == "denied":
                raise urllib.error.HTTPError(path, 403, "forbidden", Message(), None)
            return {"id": "synthetic1"}

        with (
            patch.object(preferences, "current_user", lambda environ: environ["HTTP_COOKIE"]),
            patch.object(preferences, "upstream", fake_upstream),
        ):
            own = request("userA", "synthetic1")
            assert own["status"] == "200 OK" and own["body"]["films"] == {"12": {"watched": True}}
            assert own["headers"]["Cache-Control"] == "no-store"
            assert request("userB", "synthetic1")["body"] == {"status": "unknown", "films": {}}
            assert request("denied", "synthetic1")["status"] == "403 Forbidden"
            assert request("userA", "different")["body"] == {"status": "unknown", "films": {}}
            with sqlite3.connect(preferences.DATABASE) as db:
                assert db.execute("SELECT COUNT(*) FROM preferences").fetchone()[0] == 0
            preferences.MOVARY_SIDECAR.write_text("invalid")
            assert request("userA", "synthetic1")["status"] == "503 Service Unavailable"
    print(
        "Fictional Movary sidecar: isolated users, project denial, no preference writes, no-store"
    )


if __name__ == "__main__":
    check()
