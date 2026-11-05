"""Loopback-only synthetic preference bridge authenticated by Kaneo sessions.

Run from the project root: uv run python docs/research/tracker-poc/preferences.py
The SQLite file is POC-only and must not contain actual Movary personal data.
"""

import hashlib
import hmac
import json
import secrets
import sqlite3
import urllib.error
import urllib.request
from contextlib import closing
from datetime import datetime
from pathlib import Path

from waitress import serve

ORIGIN = "http://localhost:15174"
KANEO = "http://localhost:15173/api"
DATABASE = Path(".cache/tracker-poc/preferences.sqlite3")
# ponytail: previews are process-local and expire on restart; shared state if deployed beyond the POC.
SECRET = secrets.token_bytes(32)


def upstream(path: str, cookie: str) -> dict:
    request = urllib.request.Request(KANEO + path, headers={"Cookie": cookie})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def current_user(environ: dict) -> str:
    cookie = environ.get("HTTP_COOKIE", "")
    if not cookie:
        raise PermissionError("Kaneo session required")
    try:
        session = upstream("/auth/get-session", cookie)
        user = session.get("user") if session else None
        if not user or not isinstance(user.get("id"), str):
            raise PermissionError("Kaneo session required")
        return user["id"]
    except urllib.error.HTTPError as error:
        raise PermissionError("Kaneo session required") from error


def validate(payload: dict) -> dict:
    if set(payload) != {"interest_score", "watchlist", "watched_at", "personal_notes"}:
        raise ValueError("invalid preference fields")
    score, watchlist = payload["interest_score"], payload["watchlist"]
    watched, notes = payload["watched_at"], payload["personal_notes"]
    if score is not None and (type(score) is not int or not 1 <= score <= 10):
        raise ValueError("interest score must be 1–10 or null")
    if type(watchlist) is not bool or not isinstance(notes, str) or len(notes) > 5000:
        raise ValueError("invalid watchlist or notes")
    if watched is not None and (
        not isinstance(watched, str) or datetime.fromisoformat(watched).utcoffset() is None
    ):
        raise ValueError("watched time must include a timezone")
    return payload


def load(db: sqlite3.Connection, user: str, task: str) -> dict:
    row = db.execute(
        "SELECT interest_score, watchlist, watched_at, personal_notes FROM preferences WHERE user_id=? AND task_id=?",
        (user, task),
    ).fetchone()
    return preference_from_row(row)


def preference_from_row(row) -> dict:
    return {
        "interest_score": row[0] if row else None,
        "watchlist": bool(row[1]) if row else False,
        "watched_at": row[2] if row else None,
        "personal_notes": row[3] if row else "",
    }


def preview_token(user: str, task: str, before: dict, after: dict) -> str:
    data = json.dumps([user, task, before, after], sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(SECRET, data, hashlib.sha256).hexdigest()


def respond(start, status: str, payload: dict):
    body = json.dumps(payload).encode()
    start(
        status,
        [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", ORIGIN),
            ("Access-Control-Allow-Credentials", "true"),
            ("Vary", "Origin"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def change(environ: dict, db: sqlite3.Connection, user: str, task: str) -> dict:
    cookie = environ.get("HTTP_COOKIE", "")
    try:
        upstream("/task/" + task, cookie)
    except urllib.error.HTTPError as error:
        raise PermissionError("Film is not accessible") from error
    length = int(environ.get("CONTENT_LENGTH") or 0)
    if length <= 0 or length > 16_384:
        raise ValueError("invalid request size")
    data = json.load(environ["wsgi.input"])
    proposal = validate(data["preference"])
    before = load(db, user, task)
    token = preview_token(user, task, before, proposal)
    if environ["PATH_INFO"].startswith("/preview/"):
        return {"before": before, "after": proposal, "token": token}
    if not hmac.compare_digest(str(data.get("token", "")), token):
        raise ValueError("preview required or preference changed; preview again")
    db.execute(
        "INSERT INTO preferences VALUES (?,?,?,?,?,?) ON CONFLICT(user_id,task_id) DO UPDATE SET interest_score=excluded.interest_score, watchlist=excluded.watchlist, watched_at=excluded.watched_at, personal_notes=excluded.personal_notes",
        (
            user,
            task,
            proposal["interest_score"],
            proposal["watchlist"],
            proposal["watched_at"],
            proposal["personal_notes"],
        ),
    )
    db.commit()
    return {"preference": load(db, user, task)}


def application(environ: dict, start):
    if environ.get("HTTP_ORIGIN") != ORIGIN:
        return respond(start, "403 Forbidden", {"error": "Origin not allowed"})
    if environ["REQUEST_METHOD"] == "OPTIONS":
        start(
            "204 No Content",
            [
                ("Access-Control-Allow-Origin", ORIGIN),
                ("Access-Control-Allow-Credentials", "true"),
                ("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type"),
                ("Vary", "Origin"),
            ],
        )
        return [b""]
    try:
        user = current_user(environ)
        with closing(sqlite3.connect(DATABASE)) as db:
            if environ["PATH_INFO"] == "/preferences" and environ["REQUEST_METHOD"] == "GET":
                rows = db.execute(
                    "SELECT task_id, interest_score, watchlist, watched_at, personal_notes FROM preferences WHERE user_id=?",
                    (user,),
                ).fetchall()
                return respond(
                    start,
                    "200 OK",
                    {"preferences": {row[0]: preference_from_row(row[1:]) for row in rows}},
                )
            path = environ["PATH_INFO"].split("/")
            if (
                len(path) == 3
                and path[1] in ("preview", "preferences")
                and path[2].isalnum()
                and environ["REQUEST_METHOD"] in ("POST", "PUT")
            ):
                return respond(start, "200 OK", change(environ, db, user, path[2]))
            return respond(start, "404 Not Found", {"error": "Not found"})
    except PermissionError as error:
        return respond(start, "403 Forbidden", {"error": str(error)})
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return respond(start, "400 Bad Request", {"error": "Invalid preference or preview"})
    except (urllib.error.URLError, TimeoutError):
        return respond(start, "503 Service Unavailable", {"error": "Kaneo unavailable"})


if __name__ == "__main__":
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS preferences (user_id TEXT NOT NULL, task_id TEXT NOT NULL, interest_score INTEGER, watchlist INTEGER NOT NULL, watched_at TEXT, personal_notes TEXT NOT NULL, PRIMARY KEY(user_id, task_id))"
        )
    serve(application, host="127.0.0.1", port=15175)
