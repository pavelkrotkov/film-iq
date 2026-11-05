"""Synthetic in-memory checks; never reads credentials or contacts a provider."""

import json
from datetime import UTC, datetime
from io import BytesIO

from live_bridge import (
    DESTINATIONS,
    Config,
    app,
    config_from_env,
    decode_allowlist,
    parse_allowlist,
    safe_poster,
)
from tmdb_readonly import TMDbRateLimited, read_movie

TOKEN = "fixture-token-" + "x" * 32


def invoke(application, ident, token=TOKEN):
    payload = json.dumps({"tmdb_id": ident}).encode()
    result = {}

    def start(status, headers):
        result.update(status=status, headers=dict(headers))

    result["body"] = json.loads(
        b"".join(
            application(
                {
                    "REQUEST_METHOD": "POST",
                    "PATH_INFO": "/metadata",
                    "CONTENT_LENGTH": str(len(payload)),
                    "HTTP_AUTHORIZATION": "Bearer " + token,
                    "wsgi.input": BytesIO(payload),
                },
                start,
            )
        )
    )
    assert result["headers"]["Cache-Control"] == "no-store"
    return result


def check():
    policy = {"version": 1, "allowed_ids": [101, 202], "destinations": sorted(DESTINATIONS)}
    env = {
        "FILMIQ_TMDB_BRIDGE_ENABLE_LIVE": "1",
        "FILMIQ_BRIDGE_TOKEN": TOKEN,
        "TMDB_API_KEY": "fake-key",
    }
    assert parse_allowlist(policy) == frozenset({101, 202})
    assert config_from_env(env) == Config(TOKEN)
    try:
        decode_allowlist('{"version":1,"version":1}')
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate configuration keys were accepted")
    for bad in (
        None,
        {},
        {**policy, "allowed_ids": []},
        {**policy, "allowed_ids": [True]},
        {**policy, "allowed_ids": [101, 101]},
        {**policy, "destinations": ["other.example"]},
    ):
        try:
            parse_allowlist(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid allowlist was accepted")
    for bad in (
        {},
        {**env, "FILMIQ_TMDB_BRIDGE_ENABLE_LIVE": "0"},
        {**env, "FILMIQ_BRIDGE_TOKEN": ""},
        {**env, "TMDB_API_KEY": ""},
    ):
        try:
            config_from_env(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Missing live bridge configuration was accepted")
    assert safe_poster("https://image.tmdb.org/t/p/w500/example.jpg")
    assert safe_poster("https://image.tmdb.org.evil.example/example.jpg") is None
    assert safe_poster("https://user@image.tmdb.org/example.jpg") is None

    calls = []

    def fake_get(path, parameters=None):
        calls.append(path)
        if path == "movie/202":
            raise TMDbRateLimited("fixture secret must not leak")
        if path == "movie/101":
            return {
                "id": 101,
                "title": "Fictional",
                "original_title": "Fictional original",
                "overview": "Fictional synopsis",
                "release_date": "2001-01-01",
                "genres": [],
                "credits": {"crew": []},
                "poster_path": "/example.jpg",
                "external_ids": {"imdb_id": "tt0000101"},
            }
        if path == "configuration":
            return {
                "images": {
                    "secure_base_url": "https://image.tmdb.org/t/p/",
                    "poster_sizes": ["w500"],
                }
            }
        if path == "movie/101/watch/providers":
            return {"id": 101, "results": {}}
        raise AssertionError("Unexpected provider call")

    def reader(ident):
        return read_movie(ident, get=fake_get, now=datetime(2026, 1, 1, tzinfo=UTC))

    application = app(config_from_env(env), lambda: policy, reader)
    assert invoke(application, 101, "incorrect")["status"] == "401 Unauthorized"
    assert invoke(application, 999)["status"] == "403 Forbidden"
    assert calls == []

    def missing_allowlist():
        raise FileNotFoundError("fixture path must not leak")

    missing = invoke(app(config_from_env(env), missing_allowlist, reader), 101)
    assert missing["status"] == "503 Service Unavailable" and calls == []
    assert "fixture path" not in json.dumps(missing["body"])
    ok = invoke(application, 101)
    assert ok["status"] == "200 OK"
    assert set(ok["body"]) == {
        "tmdb_id",
        "title",
        "original_title",
        "synopsis",
        "year",
        "genres",
        "directors",
        "poster_url",
        "imdb_title_url",
        "availability",
    }
    assert ok["body"]["tmdb_id"] == 101 and ok["body"]["availability"]["status"] == "unknown"
    assert ok["body"]["original_title"] == "Fictional original"
    assert ok["body"]["poster_url"] == "https://image.tmdb.org/t/p/w500/example.jpg"
    limited = invoke(application, 202)
    assert limited["status"] == "429 Too Many Requests" and "secret" not in json.dumps(
        limited["body"]
    )
    policy["allowed_ids"] = []
    count = len(calls)
    assert invoke(application, 101)["status"] == "503 Service Unavailable" and len(calls) == count
    policy["allowed_ids"] = [202]
    assert invoke(application, 101)["status"] == "403 Forbidden" and len(calls) == count
    print("Synthetic allowlist, credential, no-store, payload and 429 checks passed")


if __name__ == "__main__":
    check()
