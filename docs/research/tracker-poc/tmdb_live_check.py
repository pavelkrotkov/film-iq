"""Check read-through failures and absence of browser caching using fixtures."""

import json
import os
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import patch

from tmdb_live import app, load_allowlist
from tmdb_readonly import Movie, TMDbAccessDenied, TMDbError, TMDbRateLimited

from film_iq.availability.tmdb import Observation, Offer


def invoke(application, path, origin="http://localhost:15174"):
    result = {}

    def start(status, headers):
        result.update(status=status, headers=dict(headers))

    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "HTTP_ORIGIN": origin,
        "wsgi.input": BytesIO(),
    }
    result["body"] = json.loads(b"".join(application(environ, start)))
    return result


def check():
    policy = {
        "version": 1,
        "allowed_ids": [12],
        "destinations": ["api.themoviedb.org", "image.tmdb.org"],
    }
    calls = []
    now = datetime(2026, 11, 5, tzinfo=UTC)
    observed = Observation(
        (
            Offer(
                12,
                1,
                "Fixture Stream",
                "subscription",
                "https://www.themoviedb.org/movie/12/watch",
                now,
            ),
        ),
        "partial",
        now,
    )
    movie = Movie(
        12,
        "Fictional",
        None,
        None,
        None,
        None,
        None,
        observed,
        "https://www.imdb.com/title/tt0000012/",
        "Fictional original",
    )

    def reader(ident):
        calls.append(ident)
        return movie

    application = app(reader, lambda _: "synthetic-user", lambda: policy)
    result = invoke(application, "/movie/12")
    assert result["status"] == "200 OK"
    assert result["headers"]["Cache-Control"] == "no-store"
    assert result["body"]["availability"]["status"] == "partial"
    assert result["body"]["imdb_title_url"] == "https://www.imdb.com/title/tt0000012/"
    assert result["body"]["original_title"] == "Fictional original"
    assert result["body"]["availability"]["offers"][0]["kind"] == "subscription"
    assert invoke(application, "/movie/nope")["status"] == "404 Not Found"
    assert (
        invoke(application, "/movie/12", "https://unrelated.example")["status"] == "403 Forbidden"
    )
    assert invoke(application, "/movie/12", "null")["status"] == "403 Forbidden"
    assert invoke(application, "/movie/12", "")["status"] == "403 Forbidden"
    assert invoke(app(lambda _: movie), "/movie/12")["status"] == "401 Unauthorized"
    assert invoke(app(lambda _: movie), "/status/config")["status"] == "401 Unauthorized"
    assert invoke(application, "/movie/13")["status"] == "403 Forbidden"
    assert calls == [12]
    policy["allowed_ids"] = []
    assert invoke(application, "/movie/12")["status"] == "503 Service Unavailable"
    assert calls == [12]
    policy["allowed_ids"] = [12]
    with patch.dict(os.environ, {}, clear=True):
        unavailable = invoke(app(reader, lambda _: "synthetic-user", load_allowlist), "/movie/12")
    assert unavailable["status"] == "503 Service Unavailable"
    assert unavailable["headers"]["Cache-Control"] == "no-store"
    with patch.dict(os.environ, {"FILMIQ_APPROVAL_DIR": __file__}, clear=True):
        missing = invoke(app(reader, lambda _: "synthetic-user", load_allowlist), "/movie/12")
    assert missing["status"] == "503 Service Unavailable"
    assert calls == [12]

    def failed(_):
        raise TMDbError("secret must not be returned")

    failure = invoke(app(failed, lambda _: "synthetic-user", lambda: policy), "/movie/12")
    assert failure["status"] == "502 Bad Gateway"
    assert failure["body"] == {"error": "TMDB unavailable"}

    def denied(_):
        raise TMDbAccessDenied("secret must not be returned")

    failure = invoke(app(denied, lambda _: "synthetic-user", lambda: policy), "/movie/12")
    assert failure["status"] == "502 Bad Gateway" and failure["body"] == {
        "error": "TMDB unavailable"
    }

    def limited(_):
        raise TMDbRateLimited("secret must not be returned")

    failure = invoke(app(limited, lambda _: "synthetic-user", lambda: policy), "/movie/12")
    assert failure["status"] == "429 Too Many Requests"
    assert failure["body"] == {"error": "TMDB rate limit reached"}
    assert failure["headers"]["Cache-Control"] == "no-store"
    print("Read-through enforces approval, uses no-store, and handles failures")


if __name__ == "__main__":
    check()
