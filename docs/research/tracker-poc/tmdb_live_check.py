"""Check read-through failures and absence of browser caching using fixtures."""

import json
from datetime import UTC, datetime
from io import BytesIO

from tmdb_live import app
from tmdb_readonly import Movie, TMDbError, TMDbRateLimited

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
    movie = Movie(12, "Fictional", None, None, None, None, None, observed)
    application = app(lambda _: movie, lambda _: "synthetic-user")
    result = invoke(application, "/movie/12")
    assert result["status"] == "200 OK"
    assert result["headers"]["Cache-Control"] == "no-store"
    assert result["body"]["availability"]["status"] == "partial"
    assert result["body"]["availability"]["offers"][0]["kind"] == "subscription"
    assert invoke(application, "/movie/nope")["status"] == "404 Not Found"
    assert (
        invoke(application, "/movie/12", "https://unrelated.example")["status"] == "403 Forbidden"
    )
    assert invoke(application, "/movie/12", "null")["status"] == "403 Forbidden"
    assert invoke(application, "/movie/12", "")["status"] == "403 Forbidden"
    assert invoke(app(lambda _: movie), "/movie/12")["status"] == "401 Unauthorized"

    def failed(_):
        raise TMDbError("secret must not be returned")

    failure = invoke(app(failed, lambda _: "synthetic-user"), "/movie/12")
    assert failure["status"] == "502 Bad Gateway"
    assert failure["body"] == {"error": "TMDB unavailable"}

    def limited(_):
        raise TMDbRateLimited("secret must not be returned")

    failure = invoke(app(limited, lambda _: "synthetic-user"), "/movie/12")
    assert failure["status"] == "429 Too Many Requests"
    assert failure["body"] == {"error": "TMDB rate limit reached"}
    assert failure["headers"]["Cache-Control"] == "no-store"
    print(
        "Read-through uses no-store, preserves partial data, and rejects unsafe origin and failures"
    )


if __name__ == "__main__":
    check()
