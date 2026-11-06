"""Check fictional preferences across fresh app processes and an SQLite restore.

This exercises the real WSGI application with mocked Kaneo authentication; it
does not start a server, use an existing session, or touch the live database.
"""

import ast
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import preferences

ROOT = Path(__file__).resolve().parents[3]
SAVED = {
    "interest_score": 8,
    "watchlist": None,
    "watched_at": "2026-10-01T12:34:00+00:00",
    "personal_notes": "Fictional process recovery note.",
}
NEXT = {**SAVED, "interest_score": 9}


def request(path: str, method: str, body: dict | None = None) -> tuple[str, dict]:
    data = json.dumps(body).encode() if body is not None else b""
    environ = {
        "HTTP_ORIGIN": preferences.ORIGIN,
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(data)),
        "wsgi.input": io.BytesIO(data),
    }
    status = []
    response = preferences.application(environ, lambda code, headers: status.append(code))
    return status[0], json.loads(b"".join(response))


def worker(database: Path, mode: str) -> None:
    preferences.DATABASE = database
    with (
        patch.object(preferences, "current_user", return_value="fictionaluser"),
        patch.object(preferences, "upstream", return_value={}),
    ):
        worker_requests(mode)


def worker_requests(mode: str) -> None:
    if mode == "save":
        status, preview = request("/preview/fictionalfilm", "POST", {"preference": SAVED})
        assert status == "200 OK"
        status, result = request(
            "/preferences/fictionalfilm",
            "PUT",
            {"preference": SAVED, "token": preview["token"]},
        )
        assert status == "200 OK" and result["preference"] == SAVED
        status, preview = request("/preview/fictionalfilm", "POST", {"preference": NEXT})
        assert status == "200 OK"
        print(json.dumps({"token": preview["token"]}))
    elif mode == "verify":
        token = json.load(sys.stdin)["token"]
        status, result = request("/preferences", "GET")
        assert status == "200 OK" and result["preferences"]["fictionalfilm"] == SAVED
        status, _ = request(
            "/preferences/fictionalfilm", "PUT", {"preference": NEXT, "token": token}
        )
        assert status == "400 Bad Request"
        status, result = request("/preferences", "GET")
        assert status == "200 OK" and result["preferences"]["fictionalfilm"] == SAVED
    else:
        raise ValueError("Unknown fixture worker mode")


def run_worker(database: Path, mode: str, payload: str = "") -> str:
    result = subprocess.run(
        [sys.executable, __file__, "--worker", str(database), mode],
        cwd=ROOT,
        input=payload,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return result.stdout


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
    pending = run_worker(source, "save")
    run_worker(source, "verify", pending)
    with closing(sqlite3.connect(source)) as db, closing(sqlite3.connect(restored)) as backup:
        db.backup(backup)
        assert backup.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    run_worker(restored, "verify", pending)
    print(
        "Fictional WSGI preferences survived fresh processes and SQLite restore; stale previews were rejected."
    )
    print(f"Project-local fictional artifacts retained in {directory}")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        worker(Path(sys.argv[2]), sys.argv[3])
    else:
        main()
