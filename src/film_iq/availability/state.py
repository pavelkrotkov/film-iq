"""Read retained offer attempts, complete baseline and source-specific events."""

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime

from film_iq.availability.codec import decode_fetch, scope_key, timestamp
from film_iq.availability.fetch import Fetch
from film_iq.availability.policies import readable


def read_state(db: sqlite3.Connection, scope: Fetch, now: datetime) -> dict:
    """Denied/expired policies hide retained data immediately, before physical purge."""
    if not readable(db, scope.source, now):
        return {"latest_attempt": None, "current": None, "events": [], "first_seen_by_us": []}
    identifier, checked = scope_key(scope), timestamp(now)
    latest = db.execute(
        "SELECT payload FROM offer_fetch WHERE scope=? AND checked_at<=? AND expires_at>? "
        "ORDER BY checked_at DESC,rowid DESC LIMIT 1",
        (identifier, checked, checked),
    ).fetchone()
    current = db.execute(
        "SELECT f.payload FROM offer_current c JOIN offer_fetch f ON f.id=c.fetch_id "
        "WHERE c.scope=? AND f.checked_at<=? AND f.expires_at>?",
        (identifier, checked, checked),
    ).fetchone()
    return {
        "latest_attempt": json.loads(latest[0]) if latest else None,
        "current": json.loads(current[0]) if current else None,
        "events": [event["change"] for event in retained_events(db, now, scope=identifier)],
        "first_seen_by_us": _first_seen(db, identifier, checked),
    }


def current_opportunities(db: sqlite3.Connection, now: datetime):
    """Deduplicate actual opportunities while retaining every current source assertion."""
    from film_iq.availability.access_check import opportunities
    from film_iq.availability.codec import decode_fetch

    rows = db.execute(
        "SELECT f.source,f.payload FROM offer_current c JOIN offer_fetch f ON f.id=c.fetch_id "
        "WHERE f.checked_at<=? AND f.expires_at>?",
        (timestamp(now), timestamp(now)),
    )
    assertions = tuple(
        assertion
        for source, payload in rows
        if readable(db, source, now)
        for assertion in decode_fetch(payload).assertions
    )
    return opportunities(assertions)


def _first_seen(db, scope, now):
    seen = {}
    rows = db.execute(
        "SELECT payload FROM offer_fetch WHERE scope=? AND checked_at<=? AND expires_at>?",
        (scope, now, now),
    )
    for row in rows:
        for assertion in decode_fetch(row[0]).assertions:
            item = assertion.opportunity
            seen[item] = min(seen.get(item, assertion.checked_at), assertion.checked_at)
    return [
        {"opportunity": asdict(item), "first_seen_by_us": timestamp(checked)}
        for item, checked in sorted(seen.items(), key=lambda pair: repr(pair[0]))
    ]


def retained_events(
    db: sqlite3.Connection, now: datetime, *, scope: str | None = None
) -> list[dict]:
    """Stable event IDs, gated by current policy and every retained input deadline."""
    checked = timestamp(now)
    rows = db.execute(
        "SELECT e.id,f.source,e.payload FROM offer_event e JOIN offer_fetch f ON e.fetch_id=f.id "
        "LEFT JOIN offer_fetch p ON p.id=e.previous_fetch_id "
        "WHERE f.checked_at<=? AND f.expires_at>? AND (p.id IS NULL OR p.expires_at>?) "
        "AND (? IS NULL OR f.scope=?) ORDER BY f.checked_at,e.id",
        (checked, checked, checked, scope, scope),
    )
    return [
        {"id": identifier, "change": json.loads(payload)}
        for identifier, source, payload in rows
        if readable(db, source, now)
    ]
