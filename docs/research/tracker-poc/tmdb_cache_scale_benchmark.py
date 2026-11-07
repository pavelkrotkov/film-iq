"""Measure cache-only reads over 1,000 fictional records, without network access."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from tmdb_cache import initialize_authority, write_film
from tmdb_live_cache import MAX_AGE, LiveCache

from film_iq.retention import CachePolicy

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    now = datetime.now(UTC)
    policy = CachePolicy("TMDB", True, "Fictional test", "Fictional", now + timedelta(days=30))
    work = ROOT / ".cache/tracker-poc"
    work.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="fictional-cache-scale-", dir=work) as place:
        directory = Path(place)
        cache_root = directory / "cache"
        authority = directory / "authority.json"
        initialize_authority(cache_root, authority, policy, now - timedelta(seconds=1))
        for ident in range(1, 1001):
            write_film(
                cache_root,
                policy,
                {"tmdb_id": ident, "title": "Fictional"},
                now,
                now,
                authority=authority,
                max_age=MAX_AGE,
            )
        cache = LiveCache(directory, policy)
        for count in (130, 1000):
            start = perf_counter()
            for ident in range(1, count + 1):
                result = cache.get(ident, now)
                if result is None or result.get("title") != "Fictional":
                    raise RuntimeError("A fictional record was not returned")
            print(
                f"{count} cache-only reads with 1000 fictional records: {perf_counter() - start:.3f} s",
                flush=True,
            )


if __name__ == "__main__":
    raise SystemExit(
        "Benchmark disabled: a later run encountered a system-wide open-file error "
        "and the Mac subsequently restarted. Investigate before running it again."
    )
