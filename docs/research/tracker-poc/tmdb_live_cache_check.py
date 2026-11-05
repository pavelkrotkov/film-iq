"""Offline live-bridge cache check using fictional data and no network."""

import json
import tempfile
import urllib.error
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from email.message import Message
from importlib import import_module
from pathlib import Path

from tmdb_cache import initialize_authority, record_policy
from tmdb_live import app as kaneo_app
from tmdb_live_cache import MAX_AGE, LiveCache, from_env
from tmdb_live_check import invoke as kaneo_invoke
from tmdb_readonly import Movie, TMDbError

from film_iq.availability.tmdb import Observation, Offer
from film_iq.retention import CachePolicy

live = import_module("live_bridge")
live_check = import_module("live_bridge_check")
ROOT = Path(__file__).resolve().parents[3]


def main():
    now = datetime.now(UTC)
    policy = CachePolicy("TMDB", True, "Fictional test only", "Fictional", now + timedelta(days=30))
    approval = {"version": 1, "allowed_ids": [101], "destinations": sorted(live.DESTINATIONS)}
    with tempfile.TemporaryDirectory(
        prefix="fictional-live-cache-", dir=ROOT / ".cache/tracker-poc"
    ) as location:
        directory = Path(location)
        initialize_authority(
            directory / "cache", directory / "authority.json", policy, now - timedelta(seconds=1)
        )
        config = {**policy.__dict__, "expires_at": policy.expires_at.isoformat()}
        (directory / "policy.json").write_text(json.dumps(config))
        cache = from_env(
            {"FILMIQ_TMDB_CACHE_ENABLE": "1", "FILMIQ_TMDB_CACHE_DIRECTORY": str(directory)}
        )
        assert cache is not None and from_env({}) is None
        calls = []
        movie = Movie(
            101,
            "Fictional",
            "Fictional synopsis",
            2001,
            ("Drama",),
            (),
            None,
            Observation(
                (
                    Offer(
                        101,
                        1,
                        "Fixture Stream",
                        "subscription",
                        "https://www.themoviedb.org/movie/101/watch",
                        now,
                    ),
                ),
                "complete",
                now,
            ),
        )

        def reader(ident):
            calls.append(ident)
            return movie

        def upstream(path, cookie):
            assert cookie == ""
            if path == "/task/task-1":
                return {"id": "task-1", "title": "Fictional"}
            if path == "/custom-field/task/task-1":
                return [
                    {
                        "taskId": "task-1",
                        "fieldName": "POC TMDB ID",
                        "fieldType": "text",
                        "value": "101",
                    }
                ]
            raise urllib.error.HTTPError(path, 403, "denied", Message(), None)

        kaneo = kaneo_app(
            reader, lambda _: "fictional-user", lambda: approval, get_upstream=upstream, cache=cache
        )
        assert kaneo_invoke(kaneo, "/cache/task-1")["status"] == "404 Not Found"
        assert calls == []
        assert kaneo_invoke(kaneo, "/cache/denied")["status"] == "404 Not Found"
        assert kaneo_invoke(kaneo, "/refresh/denied")["status"] == "404 Not Found"
        assert kaneo_invoke(kaneo, "/movie/101")["status"] == "404 Not Found"
        assert calls == []

        def wrong_field(path, cookie):
            value = upstream(path, cookie)
            if isinstance(value, list):
                return [{**value[0], "taskId": "different-task"}]
            return value

        assert (
            kaneo_invoke(
                kaneo_app(
                    reader,
                    lambda _: "fictional-user",
                    lambda: approval,
                    get_upstream=wrong_field,
                    cache=cache,
                ),
                "/cache/task-1",
            )["status"]
            == "404 Not Found"
        )
        assert (
            kaneo_invoke(
                kaneo_app(
                    reader,
                    lambda _: (_ for _ in ()).throw(PermissionError()),
                    lambda: approval,
                    get_upstream=upstream,
                    cache=cache,
                ),
                "/cache/task-1",
            )["status"]
            == "401 Unauthorized"
        )
        assert kaneo_invoke(kaneo, "/refresh/task-1")["status"] == "200 OK"
        assert calls == [101]
        fetched = kaneo_invoke(kaneo, "/cache/task-1")
        assert fetched["status"] == "200 OK" and fetched["body"]["title"] == "Fictional"
        assert datetime.fromisoformat(
            fetched["body"]["cache_expires_at"]
        ) <= now + MAX_AGE + timedelta(seconds=1)
        assert calls == [101]
        other = kaneo_app(
            reader,
            lambda _: "fictional-user",
            lambda: {**approval, "allowed_ids": [102]},
            get_upstream=upstream,
            cache=cache,
        )
        assert kaneo_invoke(other, "/cache/task-1")["status"] == "404 Not Found"

        yt = live.app(live.Config(live_check.TOKEN), lambda: approval, reader, cache=cache)
        assert live_check.invoke(yt, 101, path="/cache")["status"] == "200 OK"
        assert (
            live_check.invoke(yt, 101, token="wrong", path="/cache")["status"] == "401 Unauthorized"
        )
        assert live_check.invoke(yt, 102, path="/cache")["status"] == "403 Forbidden"
        assert calls == [101]
        assert live_check.invoke(yt, 101)["status"] == "200 OK"
        assert calls == [101, 101]
        assert LiveCache(directory, policy).get(101) is not None  # new process-equivalent instance

        def failed(_):
            raise TMDbError("fixture")

        assert (
            kaneo_invoke(
                kaneo_app(
                    failed,
                    lambda _: "fictional-user",
                    lambda: approval,
                    get_upstream=upstream,
                    cache=cache,
                ),
                "/refresh/task-1",
            )["status"]
            == "502 Bad Gateway"
        )
        assert cache.get(101) is not None

        # A changed policy file cannot silently use the old in-memory decision.
        terminated = replace(policy, terminated=True, version="terminated-fixture")
        (directory / "policy.json").write_text(
            json.dumps({**terminated.__dict__, "expires_at": terminated.expires_at.isoformat()})
        )
        assert kaneo_invoke(kaneo, "/cache/task-1")["status"] == "503 Service Unavailable"
        assert kaneo_invoke(kaneo, "/refresh/task-1")["status"] == "503 Service Unavailable"
        assert live_check.invoke(yt, 101)["status"] == "503 Service Unavailable"
        assert calls == [101, 101], "A changed policy must block even a user-initiated refresh"
        record_policy(directory / "authority.json", terminated, datetime.now(UTC))
        assert cache.get(101) is None
        assert not (directory / "cache/101.json").exists()

    with tempfile.TemporaryDirectory(
        prefix="fictional-expiry-", dir=ROOT / ".cache/tracker-poc"
    ) as location:
        directory = Path(location)
        initialize_authority(
            directory / "cache", directory / "authority.json", policy, now - timedelta(seconds=1)
        )
        cache = LiveCache(directory, policy)
        from tmdb_payload import movie_payload

        cache.put(movie_payload(movie), now)
        assert cache.get(101, now + MAX_AGE - timedelta(seconds=1)) is not None
        assert cache.get(101, now + MAX_AGE) is None
        assert not (directory / "cache/101.json").exists()
    print("Offline cache TTL, live bridge authorization, restart, failure and policy checks passed")


if __name__ == "__main__":
    main()
