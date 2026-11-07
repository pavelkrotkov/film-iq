"""Loopback synthetic-only bridge. It has no route to the live TMDB provider."""

import hmac
import json
from datetime import UTC, datetime

from tmdb_readonly import TMDbRateLimited, read_movie

APPROVED_FIXTURE_IDS = frozenset({900000001, 900000002})


def fixture_get(path, parameters=None):
    if path == "movie/900000002":
        raise TMDbRateLimited("synthetic limit")
    if path == "movie/900000001":
        return {"id": 900000001, "title": "Fictional film", "overview": "Fictional synopsis"}
    if path == "configuration":
        return {}
    if path == "movie/900000001/watch/providers":
        return {"id": 900000001, "results": {}}
    raise AssertionError("Unexpected synthetic request")


def app(token, cached=None):
    if not isinstance(token, str) or not token.isascii() or not token:
        raise ValueError("Fixture token required")

    def application(environ, start):
        def send(code, value):
            body = json.dumps(value).encode()
            start(
                code,
                [
                    ("Content-Type", "application/json"),
                    ("Cache-Control", "no-store"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        auth = environ.get("HTTP_AUTHORIZATION", "")
        if (
            not isinstance(auth, str)
            or not auth.isascii()
            or not hmac.compare_digest(auth, "Bearer " + token)
        ):
            return send("401 Unauthorized", {"error": "Unauthorized"})
        if environ.get("REQUEST_METHOD") != "POST" or environ.get("PATH_INFO") != "/metadata":
            return send("404 Not Found", {"error": "Not found"})
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
            if not 0 < length <= 128:
                raise ValueError("Invalid length")
            value = json.loads(environ["wsgi.input"].read(length))
            if not isinstance(value, dict) or set(value) != {"tmdb_id"}:
                raise ValueError("Invalid input")
            ident = value["tmdb_id"]
            if type(ident) is not int or ident not in APPROVED_FIXTURE_IDS:
                return send("403 Forbidden", {"error": "Fixture ID not approved"})
        except (ValueError, UnicodeDecodeError):
            return send("400 Bad Request", {"error": "Invalid request"})
        if cached is not None:
            try:
                result = cached(ident)
            except (OSError, ValueError, PermissionError):
                return send("503 Service Unavailable", {"error": "Fixture cache unavailable"})
            if result is None:
                return send("404 Not Found", {"error": "Fixture cache miss"})
            return send("200 OK", result)
        try:
            movie = read_movie(ident, get=fixture_get, now=datetime(2026, 1, 1, tzinfo=UTC))
        except TMDbRateLimited:
            return send("429 Too Many Requests", {"error": "Provider rate limit reached"})
        except Exception:
            return send("502 Bad Gateway", {"error": "Fixture metadata unavailable"})
        return send(
            "200 OK",
            {
                "tmdb_id": movie.tmdb_id,
                "title": movie.title,
                "synopsis": movie.synopsis,
                "poster_url": movie.poster_url,
            },
        )

    return application
