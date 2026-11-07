"""Disabled-by-default seven-day cache for the two separate local POC bridges.

One process owns each directory; a lock serializes that process's threads.
Initializing the cache and reviewing retention are separate operator actions.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event, RLock, Thread

from tmdb_cache import purge_due, read_film, write_film

from film_iq.retention import CachePolicy, status

MAX_AGE = timedelta(days=7)
PURGE_INTERVAL_SECONDS = 3600


class LiveCache:
    def __init__(self, directory: Path, policy: CachePolicy, load_policy=None):
        if not directory.is_absolute() or not directory.is_dir():
            raise ValueError("An existing absolute cache directory is required")
        self.root = directory / "cache"
        self.authority = directory / "authority.json"
        self.policy = policy
        self.load_policy = load_policy
        self.lock = RLock()
        # Purge overdue sections before the bridge accepts requests.
        self._purge(datetime.now(UTC))

    def _purge(self, now: datetime) -> None:
        if self.load_policy is not None:
            self.policy = self.load_policy()
        if status(self.policy, now) == "blocked":
            raise PermissionError("Cache policy is blocked")
        actions = purge_due(self.root, self.policy, now, authority=self.authority, execute=True)
        if any("corrupt_unresolved" in sections for _, sections in actions):
            raise ValueError("Cache contains unresolved records")

    def get(self, ident: int, now: datetime | None = None) -> dict | None:
        now = now or datetime.now(UTC)
        with self.lock:
            self._purge(now)
            record = read_film(self.root, self.policy, ident, now, authority=self.authority)
            if not record or not record["metadata"]:
                return None
            metadata = dict(record["metadata"]["data"])
            poster = metadata.pop("poster_path", None)
            metadata["poster_url"] = f"https://image.tmdb.org/t/p/w500{poster}" if poster else None
            availability = record["availability"]
            expiry = min(
                record["metadata"]["expires_at"],
                availability["expires_at"] if availability else record["metadata"]["expires_at"],
            )
            return {
                "tmdb_id": ident,
                **metadata,
                "cache_expires_at": expiry,
                "availability": (
                    {**availability["data"], "checked_at": availability["observed_at"]}
                    if availability
                    else {
                        "status": "unknown",
                        "checked_at": None,
                        "provider_url": None,
                        "offers": [],
                    }
                ),
            }

    def check(self, now: datetime | None = None) -> None:
        now = now or datetime.now(UTC)
        with self.lock:
            self._purge(now)
            if not self.policy.allowed or self.policy.terminated or self.policy.expires_at <= now:
                raise PermissionError("Cache policy is not active")

    def purge(self, now: datetime | None = None) -> None:
        with self.lock:
            self._purge(now or datetime.now(UTC))

    def put(self, payload: dict, now: datetime | None = None) -> dict:
        now = now or datetime.now(UTC)
        with self.lock:
            self._purge(now)
            outcome = write_film(
                self.root, self.policy, payload, now, now, authority=self.authority, max_age=MAX_AGE
            )
            result = self.get(payload["tmdb_id"], now)
            if result is None:
                raise ValueError("Cache write could not be verified")
            if outcome["metadata"] == "preserved_incomplete":
                result["metadata_attempt"] = "incomplete"
            availability = payload.get("availability")
            attempted = availability.get("status") if isinstance(availability, dict) else None
            retained = result["availability"]["status"]
            if (attempted == "unknown" and retained in ("partial", "complete")) or (
                attempted == "partial" and retained == "complete"
            ):
                result["availability_attempt"] = attempted
            return result


def policy_file(directory: Path) -> CachePolicy:
    config = json.loads((directory / "policy.json").read_text(encoding="utf-8"))
    required = {
        "source",
        "allowed",
        "rights_evidence",
        "attribution",
        "expires_at",
        "terminated",
        "version",
    }
    if not isinstance(config, dict) or set(config) != required or config["source"] != "TMDB":
        raise ValueError("A reviewed TMDB policy is required")
    if type(config["allowed"]) is not bool or type(config["terminated"]) is not bool:
        raise ValueError("Invalid cache policy")
    return CachePolicy(
        source=config["source"],
        allowed=config["allowed"],
        rights_evidence=config["rights_evidence"],
        attribution=config["attribution"],
        expires_at=datetime.fromisoformat(config["expires_at"]),
        terminated=config["terminated"],
        version=config["version"],
    )


def from_env(env) -> LiveCache | None:
    if env.get("FILMIQ_TMDB_CACHE_ENABLE", "0") == "0":
        return None
    if env.get("FILMIQ_TMDB_CACHE_ENABLE") != "1":
        raise ValueError("Invalid cache opt-in")
    directory = Path(env.get("FILMIQ_TMDB_CACHE_DIRECTORY", ""))
    if not directory.is_absolute():
        raise ValueError("A private absolute cache directory is required")
    policy = policy_file(directory)
    cache = LiveCache(directory, policy, load_policy=lambda: policy_file(directory))
    if (
        not cache.policy.allowed
        or cache.policy.terminated
        or cache.policy.expires_at <= datetime.now(UTC)
    ):
        raise ValueError("Cache policy is not active")
    return cache


def _periodic_purge(cache, stop, interval, report_failure) -> None:
    while not stop.wait(interval):
        try:
            cache.purge()
        except Exception:
            # Never log film IDs, paths, provider data, or exception payloads.
            report_failure()


def start_purge_worker(cache, *, interval: float = PURGE_INTERVAL_SECONDS):
    """Start one idle purge worker per enabled cache; caller must stop it."""
    if cache is None:
        return None
    if interval <= 0:
        raise ValueError("Purge interval must be positive")
    stop = Event()

    def report_failure() -> None:
        logging.getLogger(__name__).error("TMDB cache maintenance failed")

    thread = Thread(
        target=_periodic_purge, args=(cache, stop, interval, report_failure), daemon=True
    )
    thread.start()

    def close() -> None:
        stop.set()
        thread.join()

    return close
