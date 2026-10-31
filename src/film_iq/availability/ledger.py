"""Atomic permitted observation storage and conservative source-change events."""

import sqlite3
from datetime import datetime

from film_iq.availability.codec import decode_fetch, encode, key, scope_key, timestamp
from film_iq.availability.fetch import Fetch
from film_iq.availability.ledger_checks import _baseline, _chronology, _initial, _validate_time
from film_iq.availability.policies import policy_for
from film_iq.availability.reconcile import changes
from film_iq.ingest.acquisition_policy import require_idle
from film_iq.retention import status


def save_fetch(db: sqlite3.Connection, fetch: Fetch, now: datetime) -> str:
    """Partial/unknown observations never replace the complete comparison baseline."""
    require_idle(db)
    policy = policy_for(db, fetch.source)
    if status(policy, now) != "retain":
        raise PermissionError("source retention is blocked, expired or terminated")
    _validate_time(fetch, now)
    payload, scope = encode(fetch), scope_key(fetch)
    identifier = key(payload)
    if db.execute("SELECT 1 FROM offer_fetch WHERE id=?", (identifier,)).fetchone():
        return identifier
    _chronology(db, fetch, scope)
    with db:
        previous = _previous(db, scope, now)
        db.execute(
            "INSERT INTO offer_fetch VALUES (?,?,?,?,?,?,?)",
            (
                identifier,
                fetch.source,
                scope,
                timestamp(fetch.checked_at),
                timestamp(policy.expires_at),
                encode(policy),
                payload,
            ),
        )
        if _baseline(fetch):
            events = changes(previous, fetch) if previous else _initial(fetch)
            _advance(db, scope, identifier, events)
    return identifier


def _previous(db, scope, now):
    row = db.execute(
        "SELECT f.payload FROM offer_current c JOIN offer_fetch f ON f.id=c.fetch_id "
        "WHERE c.scope=? AND f.expires_at>?",
        (scope, timestamp(now)),
    ).fetchone()
    return decode_fetch(row[0]) if row else None


def _advance(db, scope, identifier, events):
    db.execute(
        "INSERT INTO offer_current VALUES (?,?) ON CONFLICT(scope) "
        "DO UPDATE SET fetch_id=excluded.fetch_id",
        (scope, identifier),
    )
    db.executemany(
        "INSERT INTO offer_event VALUES (?,?,?)",
        [(key(identifier + encode(event)), identifier, encode(event)) for event in events],
    )
