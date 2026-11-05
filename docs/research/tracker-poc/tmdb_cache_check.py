"""Fictional, offline checks for the opt-in TMDB cache primitives."""

import json
import tempfile
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tmdb_cache import initialize_authority, inventory, record_policy
from tmdb_cache import purge_due as purge_impl
from tmdb_cache import read_film as read_impl
from tmdb_cache import write_film as write_impl

from film_iq.retention import CachePolicy


def require_error(function, *args) -> None:
    try:
        function(*args)
    except (ValueError, PermissionError):
        return
    raise AssertionError("Expected rejected cache operation")


def main() -> None:
    root = Path(".cache/tracker-poc")
    root.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    policy = CachePolicy(
        "TMDB",
        True,
        "fictional fixture rights",
        "fictional attribution",
        start + timedelta(days=30),
    )
    renewed = CachePolicy(
        "TMDB",
        True,
        "fictional fixture rights",
        "fictional attribution",
        start + timedelta(days=120),
    )
    film = {
        "tmdb_id": 42,
        "title": "Fictional film",
        "original_title": "Fictional original",
        "synopsis": "Fictional synopsis",
        "year": 2001,
        "genres": ["Fiction"],
        "directors": ["Fictional Director"],
        "poster_url": "https://image.tmdb.org/t/p/w500/fictional.jpg",
        "imdb_title_url": None,
        "availability": {
            "status": "complete",
            "checked_at": (start + timedelta(days=1)).isoformat(),
            "offers": [{"provider": "Fictional service", "kind": "subscription"}],
            "provider_url": None,
        },
    }
    with tempfile.TemporaryDirectory(prefix="synthetic-cache-", dir=root) as directory:
        fixture = Path(directory)
        cache, authority = fixture / "cache", fixture / "authority.json"
        initialize_authority(cache, authority, policy, start)

        def write_film(root, policy, film, observed_at, now):
            return write_impl(root, policy, film, observed_at, now, authority=authority)

        def read_film(root, policy, ident, now):
            return read_impl(root, policy, ident, now, authority=authority)

        def purge_due(root, policy, now, *, execute=False):
            return purge_impl(root, policy, now, authority=authority, execute=execute)

        sentinel = cache / "user-owned.txt"
        sentinel.write_text("do not remove", encoding="utf-8")
        now = start + timedelta(days=2)
        write_film(cache, policy, film, start, now)
        first = read_film(cache, policy, 42, now)
        assert first is not None and first["metadata"]["data"]["poster_path"] == "/fictional.jpg"
        assert "poster_url" not in first["metadata"]["data"]
        assert first["availability"]["data"]["status"] == "complete"
        assert inventory(cache) == ("42.json",)
        assert (cache / "42.json").stat().st_mode & 0o777 == 0o600

        # An unrelated pre-existing temporary path is never overwritten or removed.
        temporary = cache / "42.json.tmp"
        temporary.write_text("fictional sentinel", encoding="utf-8")
        try:
            write_film(cache, policy, film, start, now)
        except FileExistsError:
            pass
        else:
            raise AssertionError("A pre-existing temporary path was accepted")
        assert temporary.read_text(encoding="utf-8") == "fictional sentinel"
        temporary.unlink()

        original_bytes = (cache / "42.json").read_bytes()
        damaged = deepcopy(first)
        damaged["metadata"]["data"]["poster_path"] = "//untrusted.invalid/image.jpg"
        (cache / "42.json").write_text(json.dumps(damaged), encoding="utf-8")
        corrupt_bytes = (cache / "42.json").read_bytes()
        require_error(read_film, cache, policy, 42, now)
        require_error(write_film, cache, policy, film, start, now)
        assert (cache / "42.json").read_bytes() == corrupt_bytes
        (cache / "42.json").write_bytes(original_bytes)

        # Replaying the same observation under a longer policy never renews it.
        record_policy(authority, renewed, now)
        write_film(cache, renewed, film, start, now)
        assert read_film(cache, renewed, 42, now) == first
        later = deepcopy(film)
        later["synopsis"] = None
        later["availability"] = {
            "status": "partial",
            "checked_at": (start + timedelta(days=10)).isoformat(),
            "offers": [],
            "provider_url": None,
        }
        outcome = write_film(
            cache, renewed, later, start + timedelta(days=10), start + timedelta(days=10)
        )
        assert outcome["metadata"] == "preserved_incomplete"
        assert read_film(cache, renewed, 42, start + timedelta(days=10)) == first
        later["synopsis"] = "A changed fictional synopsis"
        later["poster_url"] = None
        outcome = write_film(
            cache, renewed, later, start + timedelta(days=10), start + timedelta(days=10)
        )
        assert outcome["metadata"] == "preserved_incomplete"
        assert read_film(cache, renewed, 42, start + timedelta(days=10)) == first
        later["poster_url"] = film["poster_url"]
        later["synopsis"] = ""
        write_film(cache, renewed, later, start + timedelta(days=10), start + timedelta(days=10))
        assert read_film(cache, renewed, 42, start + timedelta(days=10)) == first

        # A complete refresh has its own metadata deadline; the old complete
        # availability keeps its own earlier deadline after a partial result.
        later["synopsis"] = "Fictional updated synopsis"
        write_film(cache, renewed, later, start + timedelta(days=10), start + timedelta(days=10))
        updated = read_film(cache, renewed, 42, start + timedelta(days=10))
        assert (
            updated is not None
            and updated["metadata"]["data"]["synopsis"] == "Fictional updated synopsis"
        )
        assert updated["availability"] == first["availability"]
        boundary = start + timedelta(days=30)
        visible = read_film(cache, renewed, 42, boundary)
        assert visible is not None and visible["metadata"] and visible["availability"] is None
        require_error(write_film, cache, renewed, later, boundary, boundary)
        before = (cache / "42.json").read_bytes()
        assert purge_due(cache, renewed, boundary) == (("42.json", ("availability",)),)
        assert (cache / "42.json").read_bytes() == before
        assert purge_due(cache, renewed, boundary, execute=True) == (
            ("42.json", ("availability",)),
        )
        replay = deepcopy(later)
        replay["availability"] = film["availability"]
        write_film(cache, renewed, replay, boundary, boundary)
        after = read_film(cache, renewed, 42, boundary)
        assert after is not None and after["availability"] is None

        terminated = CachePolicy(
            "TMDB",
            True,
            "fictional fixture rights",
            "fictional attribution",
            start + timedelta(days=120),
            terminated=True,
        )
        record_policy(authority, terminated, boundary)
        assert read_film(cache, terminated, 42, boundary) is None
        assert purge_due(cache, terminated, boundary, execute=True) == (("42.json", ("metadata",)),)
        assert inventory(cache) == () and sentinel.read_text() == "do not remove"
        watermark = json.loads(authority.read_text())
        assert set(watermark) == {"version", "cache_id", "policies", "films"} and set(
            watermark["films"]
        ) == {"42"}
        assert set(watermark["films"]["42"]) == {"metadata", "availability"}
        assert "Fictional" not in json.dumps(watermark)
        record_policy(authority, renewed, boundary + timedelta(seconds=1))
        require_error(write_film, cache, renewed, film, start, boundary + timedelta(seconds=1))
        assert not (cache / "42.json").exists()
        blocked = CachePolicy(
            "TMDB",
            False,
            "fictional fixture rights",
            "fictional attribution",
            start + timedelta(days=120),
        )
        record_policy(authority, blocked, boundary + timedelta(seconds=2))
        require_error(write_film, cache, blocked, film, boundary, boundary + timedelta(seconds=2))
        assert purge_due(cache, blocked, boundary + timedelta(seconds=2), execute=True) == ()

        # Purging one film must not hide another film's still-valid observation.
        other, other_authority = fixture / "second-fixture", fixture / "second-authority.json"
        initialize_authority(other, other_authority, policy, start)
        second = {
            **film,
            "tmdb_id": 43,
            "availability": {**film["availability"], "checked_at": now.isoformat()},
        }
        write_impl(other, policy, film, start, now, authority=other_authority)
        record_policy(other_authority, renewed, now)
        write_impl(other, renewed, second, now, now, authority=other_authority)
        assert purge_impl(other, renewed, boundary, authority=other_authority, execute=True) == (
            ("42.json", ("metadata", "availability")),
        )
        assert read_impl(other, renewed, 43, boundary, authority=other_authority) is not None
    print("Fictional cache expiry, partial preservation, replay and purge checks passed")


if __name__ == "__main__":
    main()
