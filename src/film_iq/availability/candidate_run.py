"""Finite opt-in candidate acquisition; no provider winner, policy grant or scheduler."""

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.request import Request

from film_iq.availability.candidate_models import ReviewedWork
from film_iq.availability.candidate_observe import MAPPERS, observe
from film_iq.availability.candidate_transport import Response, fetch, request
from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import policy_for
from film_iq.ingest.acquisition_policy import require_idle
from film_iq.retention import status


def run_candidates(
    db: sqlite3.Connection | None,
    provider: str,
    works: list[ReviewedWork],
    *,
    max_requests: int,
    live: bool = False,
    now: datetime | None = None,
    get: Callable[[Request], Response] = fetch,
) -> dict:
    _validate(provider, works, max_requests)
    if not live:
        return {"requests": 0, "persisted": 0, "mode": "dry_run", "works": len(works)}
    if db is None:
        raise ValueError("live acquisition requires an existing policy database")
    if status(policy_for(db, provider), now or datetime.now(UTC)) != "retain":
        raise PermissionError("selected source policy is not currently allowed")
    require_idle(db)
    results = []
    for work in works:
        result = _acquire(db, provider, work, now, get)
        results.append(result)
        if _stop(result):
            break
    count = len(results)
    # Access/quota stops are explicit skipped work, never negative observations.
    results.extend(
        {"tmdb_id": work.tmdb_id, "status": "not_requested_after_stop"} for work in works[count:]
    )
    return {"requests": count, "persisted": count, "mode": "live", "results": results}


def _validate(provider: str, works: list[ReviewedWork], cap: int) -> None:
    if provider not in MAPPERS:
        raise ValueError("choose an explicit supported candidate provider")
    if type(cap) is not int or cap < 0:
        raise ValueError("max_requests must be a finite nonnegative integer")
    if len(works) > cap:
        raise ValueError("reviewed batch exceeds the explicit request cap")
    for work in works:
        work.__post_init__()
    if len({work.tmdb_id for work in works}) != len(works):
        raise ValueError("duplicate reviewed work IDs")


def _acquire(db, provider, work, now, get):
    checked = now or datetime.now(UTC)
    if status(policy_for(db, provider), checked) != "retain":
        raise PermissionError("selected source policy is not currently allowed")
    observation, error, quota = observe(provider, work, request(provider, work), checked, get)
    identifier = save_fetch(db, observation, now or datetime.now(UTC))
    return {
        "tmdb_id": work.tmdb_id,
        "status": observation.status,
        "fetch_id": identifier,
        "error_code": error,
        "quota_remaining": quota,
    }


def _stop(result: dict) -> bool:
    return (
        result["error_code"] in {"http_401", "http_403", "http_429"}
        or 0 in result["quota_remaining"].values()
    )
