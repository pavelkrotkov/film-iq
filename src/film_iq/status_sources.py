"""Read-only summaries of acquisition cursors and explicit provider policies."""

import sqlite3
from collections import Counter
from contextlib import closing
from datetime import datetime
from pathlib import Path

from film_iq.availability.codec import decode_policy
from film_iq.ingest.acquisition import acquisition_status
from film_iq.retention import status
from film_iq.status_run import checked_time


def _open(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def source_status(path: Path, now: datetime) -> dict:
    with closing(_open(path)) as db:
        records = acquisition_status(db)
    outcomes = Counter(row["outcome"] or "unknown" for row in records)
    attention = sum(count for outcome, count in outcomes.items() if outcome != "success")
    return {
        "state": "attention" if attention else "observed" if records else "empty",
        "sources": len(records),
        "attempts_needing_attention": attention,
        "running": outcomes["running"],
        "failed": outcomes["error"],
        "cursors_present": sum(row["cursor"] is not None for row in records),
        "last_successful_acquisition": _last_success(records, now),
    }


def _last_success(records, now):
    stamps = []
    for row in records:
        stamp = checked_time(row["succeeded_at"], now)
        if stamp is not None:
            stamps.append(stamp)
    return max(stamps, default=None)


def provider_status(path: Path, now: datetime) -> dict:
    with closing(_open(path)) as db:
        policies = [decode_policy(row[0]) for row in db.execute("SELECT payload FROM offer_policy")]
    states = Counter(status(policy, now) for policy in policies)
    return {
        "state": "attention"
        if states["blocked"] + states["purge_due"]
        else "observed"
        if policies
        else "not_configured",
        "policies": len(policies),
        "permitted": states["retain"],
        "blocked": states["blocked"],
        "purge_due": states["purge_due"],
    }
