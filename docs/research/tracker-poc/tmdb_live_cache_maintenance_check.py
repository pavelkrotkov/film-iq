"""Exercise cache maintenance with fictional files and no provider requests."""

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event
from unittest.mock import patch

from tmdb_cache import initialize_authority, record_policy, write_film
from tmdb_live_cache import MAX_AGE, LiveCache, _periodic_purge, from_env, start_purge_worker

from film_iq.retention import CachePolicy

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    class Stop:
        def __init__(self):
            self.calls = 0

        def wait(self, _interval):
            self.calls += 1
            return self.calls > 2

    class FakeCache:
        def __init__(self):
            self.calls = 0

        def purge(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("fictional secret must not appear")

    fake, stop, failures = FakeCache(), Stop(), []
    _periodic_purge(fake, stop, 3600, lambda: failures.append("generic"))
    assert fake.calls == 2 and failures == ["generic"]
    with patch("tmdb_live_cache.Thread") as thread:
        assert start_purge_worker(None) is None
        thread.assert_not_called()

    started = Event()

    class SignalCache:
        def purge(self):
            started.set()

    close = start_purge_worker(SignalCache(), interval=0.01)
    assert close is not None and started.wait(2)
    close()

    reported = Event()

    class FailingCache:
        def purge(self):
            raise RuntimeError("fictional secret must not appear")

    with patch("tmdb_live_cache.logging.getLogger") as get_logger:
        get_logger.return_value.error.side_effect = lambda *_: reported.set()
        close = start_purge_worker(FailingCache(), interval=0.01)
        assert close is not None and reported.wait(2)
        close()
        get_logger.return_value.error.assert_called_with("TMDB cache maintenance failed")

    now = datetime.now(UTC)
    observation = now - timedelta(days=8)
    policy = CachePolicy("TMDB", True, "Fictional test", "Fictional", now + timedelta(days=30))
    with tempfile.TemporaryDirectory(
        prefix="fictional-maintenance-", dir=ROOT / ".cache/tracker-poc"
    ) as place:
        directory = Path(place)
        root, authority = directory / "cache", directory / "authority.json"
        initialize_authority(root, authority, policy, observation - timedelta(seconds=1))
        (directory / "policy.json").write_text(
            json.dumps({**policy.__dict__, "expires_at": policy.expires_at.isoformat()})
        )
        payload = {
            "tmdb_id": 987654321,
            "title": "Fictional",
            "availability": {
                "status": "complete",
                "checked_at": observation.isoformat(),
                "offers": [],
            },
        }
        write_film(
            root, policy, payload, observation, observation, authority=authority, max_age=MAX_AGE
        )
        record = root / "987654321.json"
        command = [
            sys.executable,
            str(ROOT / "docs/research/tracker-poc/tmdb_live_cache_purge.py"),
            "--directory",
            str(directory),
        ]
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        denied = subprocess.run(command, capture_output=True, text=True, env=env, timeout=15)
        assert denied.returncode != 0 and record.is_file()
        preview = subprocess.run(
            [*command, "--writers-stopped"], capture_output=True, text=True, env=env, timeout=15
        )
        assert (
            preview.returncode == 0
            and "Would purge: 1 records" in preview.stdout
            and record.is_file()
        )
        assert "987654321" not in preview.stdout and str(directory) not in preview.stdout
        result = subprocess.run(
            [*command, "--writers-stopped", "--execute"],
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
        )
        assert (
            result.returncode == 0 and "Purged: 1 records" in result.stdout and not record.exists()
        )
        assert "987654321" not in result.stdout and str(directory) not in result.stdout

        # The public purge entry point acquires the same lock used for reads/writes.
        cache = LiveCache(directory, policy)

        class CountingLock:
            def __init__(self):
                self.entries = 0

            def __enter__(self):
                self.entries += 1

            def __exit__(self, *_):
                pass

        lock = CountingLock()
        with patch.object(cache, "lock", lock):
            cache.purge(now)
        assert lock.entries == 1

        corrupt = root / "987654321.json"
        corrupt.write_text("fictional corrupt data")
        unresolved = subprocess.run(
            [*command, "--writers-stopped", "--execute"],
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
        )
        assert (
            unresolved.returncode == 1
            and "Purged: 0 records; 0 sections; unresolved: 1." in unresolved.stdout
        )
        assert corrupt.is_file() and "987654321" not in unresolved.stdout
        (directory / "policy.json").write_text(
            json.dumps(
                {**policy.__dict__, "allowed": False, "expires_at": policy.expires_at.isoformat()}
            )
        )
        blocked = subprocess.run(
            [*command, "--writers-stopped", "--execute"],
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
        )
        assert blocked.returncode == 1 and "blocked" in blocked.stdout and corrupt.is_file()

    with tempfile.TemporaryDirectory(
        prefix="fictional-idle-purge-", dir=ROOT / ".cache/tracker-poc"
    ) as place:
        directory = Path(place)
        root, authority = directory / "cache", directory / "authority.json"
        initialize_authority(root, authority, policy, now - timedelta(seconds=1))
        cache = LiveCache(directory, policy)
        payload = {
            "tmdb_id": 987654321,
            "title": "Fictional",
            "availability": {"status": "complete", "checked_at": now.isoformat(), "offers": []},
        }
        cache.put(payload, now)
        purged = Event()

        class FuturePurge:
            def purge(self):
                cache.purge(now + MAX_AGE)
                purged.set()

        close = start_purge_worker(FuturePurge(), interval=0.01)
        assert close is not None and purged.wait(2)
        close()
        assert not (root / "987654321.json").exists()

    with tempfile.TemporaryDirectory(
        prefix="fictional-blocked-purge-", dir=ROOT / ".cache/tracker-poc"
    ) as place:
        directory = Path(place)
        root, authority = directory / "cache", directory / "authority.json"
        initialize_authority(root, authority, policy, now - timedelta(seconds=1))
        config = {**policy.__dict__, "expires_at": policy.expires_at.isoformat()}
        (directory / "policy.json").write_text(json.dumps(config))
        blocked_cache = from_env(
            {"FILMIQ_TMDB_CACHE_ENABLE": "1", "FILMIQ_TMDB_CACHE_DIRECTORY": str(directory)}
        )
        assert blocked_cache is not None
        blocked_cache.put({"tmdb_id": 987654321, "title": "Fictional"}, now)
        blocked = replace(policy, allowed=False, version="blocked-fixture")
        record_policy(authority, blocked, datetime.now(UTC))
        (directory / "policy.json").write_text(
            json.dumps({**config, "allowed": False, "version": blocked.version})
        )
        reported = Event()
        with patch("tmdb_live_cache.logging.getLogger") as get_logger:
            get_logger.return_value.error.side_effect = lambda *_: reported.set()
            close = start_purge_worker(blocked_cache, interval=0.01)
            assert close is not None and reported.wait(2)
            close()
            get_logger.return_value.error.assert_called_with("TMDB cache maintenance failed")
        assert (root / "987654321.json").is_file(), "Blocked policy must not delete retained data"
    print("Fictional hourly and stopped-writer purge checks passed")


if __name__ == "__main__":
    main()
