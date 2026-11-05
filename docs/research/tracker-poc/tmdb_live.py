"""Optional loopback TMDB read-through; stores no responses or credentials.

This service only returns public movie metadata, not personal film data. It is
an experiment, not a rights certification. Supply the existing TMDB credential
in the process environment and stop the service when testing is finished.
"""

import json
import os
import sys
from importlib import import_module
from pathlib import Path

from preferences import current_user
from tmdb_payload import movie_payload
from tmdb_readonly import TMDbError, TMDbRateLimited, read_movie
from waitress import serve

ALLOWED_ORIGINS = {"http://localhost:15174"}
sys.path.append(str(Path(__file__).resolve().parent / "youtrack-tmdb-live-bridge"))
approval = import_module("live_bridge")


def load_allowlist():
    directory = os.environ.get("FILMIQ_APPROVAL_DIR")
    if not directory:
        raise ValueError("Approval configuration unavailable")
    path = Path(directory) / "approved-ids.json"
    return approval.decode_allowlist(path.read_text(encoding="utf-8"))


def response(start, status: str, payload: dict, origin: str):
    body = json.dumps(payload).encode()
    headers = [
        ("Content-Type", "application/json"),
        ("Cache-Control", "no-store"),
        ("Vary", "Origin"),
        ("Content-Length", str(len(body))),
    ]
    if origin in ALLOWED_ORIGINS:
        headers.append(("Access-Control-Allow-Origin", origin))
        headers.append(("Access-Control-Allow-Credentials", "true"))
    start(status, headers)
    return [body]


def app(reader=read_movie, authenticate=current_user, load_approval=load_allowlist):
    def application(environ: dict, start):
        origin = environ.get("HTTP_ORIGIN", "")
        if origin not in ALLOWED_ORIGINS:
            return response(start, "403 Forbidden", {"error": "Origin not allowed"}, origin)
        path = environ.get("PATH_INFO", "").split("/")
        if (
            environ.get("REQUEST_METHOD") != "GET"
            or len(path) != 3
            or path[1] != "movie"
            or not path[2].isascii()
            or not path[2].isdigit()
            or not 0 < int(path[2]) <= 2_147_483_647
        ):
            return response(start, "404 Not Found", {"error": "Not found"}, origin)
        try:
            authenticate(environ)
        except (PermissionError, OSError, ValueError):
            return response(start, "401 Unauthorized", {"error": "Kaneo session required"}, origin)
        try:
            allowed = approval.parse_allowlist(load_approval())
        except (OSError, ValueError, TypeError):
            return response(
                start,
                "503 Service Unavailable",
                {"error": "Approval configuration unavailable"},
                origin,
            )
        if int(path[2]) not in allowed:
            return response(start, "403 Forbidden", {"error": "Film not approved"}, origin)
        try:
            movie = reader(int(path[2]))
        except TMDbRateLimited:
            return response(
                start, "429 Too Many Requests", {"error": "TMDB rate limit reached"}, origin
            )
        except (TMDbError, ValueError, OSError):
            return response(start, "502 Bad Gateway", {"error": "TMDB unavailable"}, origin)
        return response(start, "200 OK", movie_payload(movie), origin)

    return application


if __name__ == "__main__":
    serve(app(), host="127.0.0.1", port=15176)
