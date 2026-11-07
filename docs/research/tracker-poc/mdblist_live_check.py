"""Deterministic synthetic contract checks; never reads the real API key."""

import json
import urllib.error
import urllib.parse
from email.message import Message
from unittest.mock import patch

import mdblist_live as app


class Key:
    def read_text(self):
        return "fixture-key"


class Response:
    def __init__(self, payload):
        self.raw = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, _maximum):
        return self.raw


class Opener:
    def __init__(self, payload):
        self.payload = payload

    def open(self, request, timeout):
        assert timeout == 20
        url = urllib.parse.urlsplit(request.full_url)
        assert url.scheme == "https" and url.hostname == "api.mdblist.com"
        assert url.path == "/tmdb/movie/42/"
        assert urllib.parse.parse_qs(url.query) == {"apikey": ["fixture-key"]}
        return Response(self.payload)


def fixture():
    return {
        "tmdbid": 42,
        "ratings": [
            {
                "source": "tomatoes",
                "value": 80,
                "score": 80,
                "votes": 30,
                "url": "https://www.rottentomatoes.com/m/synthetic",
            },
            {
                "source": "popcorn",
                "value": 70,
                "score": 70,
                "votes": 12,
                "url": "https://www.rottentomatoes.com/m/synthetic",
            },
            {
                "source": "metacritic",
                "value": 84,
                "score": 84,
                "votes": None,
                "url": "https://evil.invalid/forged",
            },
            {"source": "unknown_source", "value": None, "score": None, "url": None},
        ],
    }


def request(environ):
    status = []

    def start(code, headers):
        status.append((code, dict(headers)))

    data = b"".join(app.application(environ, start))
    return status[0], json.loads(data)


def main():
    result = app.fetch_movie(42, Key(), Opener(fixture()))
    assert result["tmdb_id"] == 42
    assert [(r["source"], r["kind"]) for r in result["ratings"]] == [
        ("tomatoes", "critic"),
        ("popcorn", "audience"),
        ("metacritic", "critic"),
        ("unknown_source", "unknown"),
    ]
    assert result["ratings"][0]["url"].startswith("https://www.rottentomatoes.com/")
    assert result["ratings"][2]["url"] is None and result["ratings"][3]["value"] is None
    assert all(r["via"] == "MDBList" for r in result["ratings"])
    for invalid in ({**fixture(), "tmdbid": 43}, {**fixture(), "tmdbid": "42"}, {"ratings": []}):
        try:
            app.normalize(invalid, 42)
        except app.MDBListError:
            pass
        else:
            raise AssertionError("Mismatched or absent identity was accepted")

    class Failing:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(request.full_url, 429, "secret in error", Message(), None)

    try:
        app.fetch_movie(42, Key(), Failing())
    except app.MDBListError as error:
        assert "fixture-key" not in str(error) and "secret in error" not in str(error)
        assert "rate limit" in str(error)
    else:
        raise AssertionError("Rate limit was not surfaced")

    env = {"HTTP_ORIGIN": app.ORIGIN, "REQUEST_METHOD": "GET", "PATH_INFO": "/ratings/42"}
    with (
        patch.object(app, "current_user", return_value="fixture-user"),
        patch.object(app, "fetch_movie", return_value=result),
    ):
        (status, headers), data = request(env)
        assert status == "200 OK" and headers["Cache-Control"] == "no-store"
        assert headers["Access-Control-Allow-Origin"] == app.ORIGIN and data == result
        assert request({**env, "HTTP_ORIGIN": "https://example.invalid"})[0][0] == "403 Forbidden"
        assert request({**env, "PATH_INFO": "/ratings/0"})[0][0] == "404 Not Found"
        assert request({**env, "REQUEST_METHOD": "POST"})[0][0] == "405 Method Not Allowed"
    with patch.object(app, "current_user", side_effect=PermissionError("private token")):
        assert request(env)[1] == {"error": "Kaneo session required"}
    print("Synthetic MDBList identity, ratings, links, sanitization and loopback checks passed")


if __name__ == "__main__":
    main()
