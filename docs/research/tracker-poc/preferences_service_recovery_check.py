"""Check fictional preferences across Waitress restarts and SQLite restore.

Tracker authentication is mocked; no existing session or live database is used.
"""

import ast
import json
import os
import select
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from contextlib import closing, contextmanager
from pathlib import Path
from unittest.mock import patch

import preferences
from waitress import create_server

ROOT = Path(__file__).resolve().parents[3]
SAVED = {
    "interest_score": 8,
    "watchlist": None,
    "watched_at": "2026-10-01T12:34:00+00:00",
    "personal_notes": "Fictional process recovery note.",
}
NEXT = {**SAVED, "interest_score": 9}


def worker(database: Path) -> None:
    preferences.DATABASE = database
    preferences.MOVARY_WATCHLIST_SIDECAR = database.parent / "watchlist.json"
    with (
        patch.object(preferences, "current_user", return_value="fictionaluser"),
        patch.object(preferences, "upstream", return_value={}),
    ):
        server = create_server(preferences.application, host="127.0.0.1", port=0)
        print(server.effective_port, flush=True)
        server.run()


@contextmanager
def service(database: Path):
    process = subprocess.Popen(
        [sys.executable, __file__, "--worker", str(database)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    try:
        assert process.stdout is not None
        ready, _, _ = select.select([process.stdout], [], [], 10)
        if not ready:
            raise RuntimeError("Fictional Waitress service did not start")
        port = process.stdout.readline().strip()
        if not port.isdigit():
            raise RuntimeError("Fictional Waitress service could not bind")
        yield int(port)
    finally:
        process.terminate()
        process.wait(timeout=10)
        if process.stdout is not None:
            process.stdout.close()


def request(port: int, path: str, method: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    query = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data,
        {"Origin": preferences.ORIGIN, "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(query, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        with error:
            return error.code, json.load(error)


def verify(port: int, token: str) -> None:
    status, result = request(port, "/preferences", "GET")
    assert status == 200 and result["preferences"]["fictionalfilm"] == SAVED
    status, _ = request(
        port, "/preferences/fictionalfilm", "PUT", {"preference": NEXT, "token": token}
    )
    assert status == 400
    status, result = request(port, "/preferences", "GET")
    assert status == 200 and result["preferences"]["fictionalfilm"] == SAVED


def main() -> None:
    cache = ROOT / ".cache/tracker-poc"
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="fictional-pref-process-recovery-", dir=cache))
    source, restored = (directory / name for name in ("source.sqlite3", "restored.sqlite3"))
    tree = ast.parse(Path(preferences.__file__).read_text())
    schemas = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("CREATE TABLE IF NOT EXISTS preferences (")
    ]
    if len(schemas) != 1:
        raise RuntimeError("Cannot uniquely identify the current POC schema")
    for path in (source, restored):
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    with closing(sqlite3.connect(source)) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(schemas[0])
        db.commit()
    with service(source) as port:
        status, preview = request(port, "/preview/fictionalfilm", "POST", {"preference": SAVED})
        assert status == 200
        status, result = request(
            port,
            "/preferences/fictionalfilm",
            "PUT",
            {"preference": SAVED, "token": preview["token"]},
        )
        assert status == 200 and result["preference"] == SAVED
        status, preview = request(port, "/preview/fictionalfilm", "POST", {"preference": NEXT})
        assert status == 200
        pending = preview["token"]
    with service(source) as port:
        verify(port, pending)
        with closing(sqlite3.connect(source)) as db, closing(sqlite3.connect(restored)) as backup:
            db.backup(backup)
            assert backup.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    with service(restored) as port:
        verify(port, pending)
    print(
        "Fictional Waitress preferences survived restart and SQLite restore; stale previews were rejected."
    )
    print(f"Project-local fictional artifacts retained in {directory}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(Path(sys.argv[2]))
    else:
        main()
