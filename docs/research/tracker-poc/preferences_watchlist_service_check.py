"""Fictional live HTTP watchlist read across a preference-bridge restart.

Authentication and project access are mocked by the existing test worker.
No real tracker session, Movary data or provider is used.
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

from preferences_service_recovery_check import ROOT, request, service


def main():
    directory = Path(
        tempfile.mkdtemp(prefix="fictional-watchlist-process-", dir=ROOT / ".cache/tracker-poc")
    )
    database, sidecar = directory / "preferences.sqlite3", directory / "watchlist.json"
    with sqlite3.connect(database) as db:
        db.execute(
            "CREATE TABLE preferences (user_id,task_id,interest_score,watchlist,watched_at,personal_notes)"
        )
    database.chmod(0o600)
    view = {
        "version": "tracker-poc-movary-watchlist-v1",
        "source": "Movary",
        "observed_at": "2026-11-06T12:00:00Z",
        "entries": [{"tmdb_id": 42, "title": "Fictional film", "added_at": "2026-11-01 09:02:03"}],
    }
    sidecar.write_text(
        json.dumps(
            {
                "version": "tracker-poc-movary-watchlist-users-v1",
                "project_id": "fictional1",
                "users": {"fictionaluser": view},
            }
        )
    )
    sidecar.chmod(0o600)
    original = sidecar.read_bytes()
    for _ in range(2):
        with service(database) as port:
            code, response = request(port, "/movary-watchlist/fictional1", "GET")
            assert code == 200 and response == {
                "status": "available",
                "source": "Movary",
                "observed_at": view["observed_at"],
                "entries": view["entries"],
            }
            code, response = request(port, "/movary-watchlist/different", "GET")
            assert code == 200 and response["status"] == "unknown" and response["entries"] == []
            assert sidecar.read_bytes() == original
    assert os.stat(sidecar).st_mode & 0o777 == 0o600
    print("Fictional project-scoped watchlist survived actual HTTP service restart; auth mocked")


if __name__ == "__main__":
    main()
