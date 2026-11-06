"""Offline live-bridge cache check using fictional data and no network."""

import json
import tempfile
import urllib.error
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from email.message import Message
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

import tmdb_cache
from tmdb_cache import _load, initialize_authority, record_policy
from tmdb_live import app as kaneo_app
from tmdb_live_cache import MAX_AGE, LiveCache, from_env
from tmdb_live_cache_downgrade import downgrade
from tmdb_live_check import invoke as kaneo_invoke
from tmdb_payload import movie_payload
from tmdb_readonly import Movie, TMDbAccessDenied, TMDbError

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
        initial = kaneo_invoke(kaneo, "/refresh/task-1")
        assert initial["status"] == "200 OK"
        assert "metadata_attempt" not in initial["body"]
        assert "availability_attempt" not in initial["body"]
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

        paused_kaneo = kaneo_app(
            reader,
            lambda _: "fictional-user",
            lambda: approval,
            get_upstream=upstream,
            cache=cache,
            load_catalog_approval=lambda: approval,
            read_catalog=lambda *_: {"status": "fictional"},
            refresh_enabled=False,
            pace_enabled=True,
        )
        assert kaneo_invoke(paused_kaneo, "/status/config")["body"] == {
            "pace_enabled": True,
            "refresh_enabled": False,
        }
        assert kaneo_invoke(paused_kaneo, "/refresh/task-1")["status"] == "503 Service Unavailable"
        assert kaneo_invoke(paused_kaneo, "/cache/task-1")["status"] == "200 OK"
        assert kaneo_invoke(paused_kaneo, "/catalog/task-1")["status"] == "200 OK"
        assert calls == [101], "Paused refresh or status must not call the provider"

        yt = live.app(live.Config(live_check.TOKEN), lambda: approval, reader, cache=cache)
        assert live_check.invoke(yt, 101, path="/cache")["status"] == "200 OK"
        assert (
            live_check.invoke(yt, 101, token="wrong", path="/cache")["status"] == "401 Unauthorized"
        )
        assert live_check.invoke(yt, 102, path="/cache")["status"] == "403 Forbidden"
        assert calls == [101]
        paused_yt = live.app(
            live.Config(live_check.TOKEN),
            lambda: approval,
            reader,
            catalog_reader=lambda *_: {"status": "fictional"},
            cache=cache,
            refresh_enabled=False,
            pace_enabled=True,
        )
        assert live_check.invoke(paused_yt, 101, path="/status")["body"] == {
            "pace_enabled": True,
            "refresh_enabled": False,
        }
        assert (
            live_check.invoke(paused_yt, 101, token="wrong", path="/status")["status"]
            == "401 Unauthorized"
        )
        assert live_check.invoke(paused_yt, 102, path="/status")["status"] == "403 Forbidden"
        assert live_check.invoke(paused_yt, 101)["status"] == "503 Service Unavailable"
        assert live_check.invoke(paused_yt, 101, path="/cache")["status"] == "200 OK"
        assert (
            live_check.invoke(paused_yt, 101, path="/catalog", title="Fictional")["status"]
            == "200 OK"
        )
        assert calls == [101], "Paused refresh or status must not call the provider"
        initial_yt = live_check.invoke(yt, 101)
        assert initial_yt["status"] == "200 OK"
        assert "metadata_attempt" not in initial_yt["body"]
        assert "availability_attempt" not in initial_yt["body"]
        assert calls == [101, 101]
        assert LiveCache(directory, policy).get(101) is not None  # new process-equivalent instance

        # A provider authorization failure must stop a batch and retain the
        # earlier cached metadata and availability without exposing secrets.
        prior = cache.get(101)

        def denied(_):
            raise TMDbAccessDenied("fictional credential must not escape")

        denied_kaneo = kaneo_app(
            denied, lambda _: "fictional-user", lambda: approval, get_upstream=upstream, cache=cache
        )
        denied_yt = live.app(live.Config(live_check.TOKEN), lambda: approval, denied, cache=cache)
        for result in (
            kaneo_invoke(denied_kaneo, "/refresh/task-1"),
            live_check.invoke(denied_yt, 101),
        ):
            assert result["status"] == "403 Forbidden"
            assert result["body"] == {"error": "Metadata access denied"}
            assert cache.get(101) == prior

        # A refresh can omit an existing synopsis and return only partial
        # availability. Both endpoints must show the same retained values as
        # their next cache read, even if the page has no previous UI state.
        for attempted in ("partial", "unknown"):
            incomplete = replace(
                movie,
                synopsis=None,
                availability=Observation((), attempted, datetime.now(UTC)),
            )
            partial_kaneo = kaneo_app(
                lambda _, result=incomplete: result,
                lambda _: "fictional-user",
                lambda: approval,
                get_upstream=upstream,
                cache=cache,
            )
            partial_yt = live.app(
                live.Config(live_check.TOKEN),
                lambda: approval,
                lambda _, result=incomplete: result,
                cache=cache,
            )
            for result in (
                kaneo_invoke(partial_kaneo, "/refresh/task-1"),
                live_check.invoke(partial_yt, 101),
            ):
                assert result["status"] == "200 OK"
                assert result["body"]["synopsis"] == "Fictional synopsis"
                assert result["body"]["availability"]["status"] == "complete"
                assert result["body"]["availability_attempt"] == attempted
                assert result["body"]["metadata_attempt"] == "incomplete"

        # A genuine unknown is an attempted check, not a negative provider
        # result. Its timestamp must survive a cache read/restart.
        checked_at = datetime.now(UTC)
        unknown_movie = replace(
            movie, tmdb_id=102, availability=Observation((), "unknown", checked_at)
        )
        unknown_response = cache.put(movie_payload(unknown_movie))
        assert unknown_response["availability"]["status"] == "unknown"
        assert unknown_response["availability"]["checked_at"] == checked_at.isoformat()
        unknown_after_reload = cache.get(102)
        assert unknown_after_reload and unknown_after_reload["availability"] == {
            "status": "unknown",
            "checked_at": checked_at.isoformat(),
            "provider_url": None,
            "offers": [],
        }
        restarted_unknown = LiveCache(directory, policy).get(102)
        assert (
            restarted_unknown
            and restarted_unknown["availability"] == unknown_after_reload["availability"]
        )

        # A partial observation survives a later unknown attempt; the old
        # timestamp remains the observation time and the attempt is labeled.
        partial_time = datetime.now(UTC)
        partial_movie = replace(
            movie, tmdb_id=103, availability=Observation((), "partial", partial_time)
        )
        cache.put(movie_payload(partial_movie))
        later_unknown = replace(
            partial_movie, availability=Observation((), "unknown", datetime.now(UTC))
        )
        retained_partial = cache.put(movie_payload(later_unknown))
        assert retained_partial["availability"]["status"] == "partial"
        assert retained_partial["availability"]["checked_at"] == partial_time.isoformat()
        assert retained_partial["availability_attempt"] == "unknown"
        partial_after_reload = cache.get(103)
        assert (
            partial_after_reload
            and partial_after_reload["availability"] == retained_partial["availability"]
        )

        # Rollback is a stopped-writer, preview-first operation. Only unknown
        # sections are removed; known observations and authority stay byte-identical.
        authority_before = (directory / "authority.json").read_bytes()
        known_before = {i: (directory / "cache" / f"{i}.json").read_bytes() for i in (101, 103)}
        unknown_before = _load(directory / "cache/102.json", 102)
        try:
            downgrade(Path("/"), execute=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Downgrade allowed a non-project directory")
        # Validate every file before changing any: one corrupt record must
        # abort the operation without changing even the unknown observation.
        fixture_path = directory / "cache/103.json"
        fixture_path.write_text("invalid fictional JSON", encoding="utf-8")
        try:
            downgrade(directory / "cache", execute=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Downgrade accepted a corrupt record")
        assert _load(directory / "cache/102.json", 102) == unknown_before
        fixture_path.write_bytes(known_before[103])
        # Emulate the old reader: before downgrade its validator rejects the
        # new section, and after downgrade all records remain readable.
        validator = tmdb_cache._availability

        def legacy_availability(value, now):
            return None if value.get("status") == "unknown" else validator(value, now)

        with patch.object(tmdb_cache, "_availability", side_effect=legacy_availability):
            try:
                _load(directory / "cache/102.json", 102)
            except ValueError:
                pass
            else:
                raise AssertionError("Old reader unexpectedly accepted unknown availability")
        assert downgrade(directory / "cache") == 1
        assert _load(directory / "cache/102.json", 102) == unknown_before
        assert downgrade(directory / "cache", execute=True) == 1
        downgraded = _load(directory / "cache/102.json", 102)
        assert downgraded == {**unknown_before, "availability": None}
        assert (directory / "authority.json").read_bytes() == authority_before
        assert all(
            (directory / "cache" / f"{i}.json").read_bytes() == raw
            for i, raw in known_before.items()
        )
        assert downgrade(directory / "cache", execute=True) == 0
        with patch.object(tmdb_cache, "_availability", side_effect=legacy_availability):
            for ident in (101, 102, 103):
                _load(directory / "cache" / f"{ident}.json", ident)

        # An unknown containing offers or a provider URL is invalid and must
        # not be retained as if it were a successful or negative observation.
        for ident, extra in (
            (104, {"offers": [{"provider": "Fixture Stream", "kind": "subscription"}]}),
            (105, {"provider_url": "https://www.themoviedb.org/movie/105/watch"}),
        ):
            invalid = movie_payload(replace(unknown_movie, tmdb_id=ident))
            invalid["availability"].update(extra)
            rejected = cache.put(invalid)
            assert rejected["availability"]["checked_at"] is None
            result = cache.get(ident)
            assert result and result["availability"] == {
                "status": "unknown",
                "checked_at": None,
                "provider_url": None,
                "offers": [],
            }

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
        cache.put(movie_payload(movie), now)
        assert cache.get(101, now + MAX_AGE - timedelta(seconds=1)) is not None
        # Unknown attempts expire on the same deadline, even if another
        # metadata-only refresh extends the metadata section.
        expiry_film = movie_payload(
            replace(movie, tmdb_id=106, availability=Observation((), "unknown", now))
        )
        cache.put(expiry_film, now)
        metadata_only = {**expiry_film, "availability": {"status": "unknown", "offers": []}}
        cache.put(metadata_only, now + MAX_AGE - timedelta(seconds=1))
        expired_unknown = cache.get(106, now + MAX_AGE)
        assert expired_unknown and expired_unknown["availability"]["checked_at"] is None
        assert cache.get(101, now + MAX_AGE) is None
        assert not (directory / "cache/101.json").exists()
    print("Offline cache TTL, live bridge authorization, restart, failure and policy checks passed")


if __name__ == "__main__":
    main()
