"""A new batch cannot extend a cached assertion's previously frozen retention."""

import sqlite3
from datetime import datetime

from film_iq.availability.codec import decode_fetch, timestamp
from film_iq.availability.fetch import Fetch


def input_deadline(
    db: sqlite3.Connection, fetch: Fetch, permitted_until: datetime, now: datetime
) -> str:
    """Bound the stored batch by any retained source/check-time inputs it reuses.

    Assertion check times identify actual source observations; an enclosing batch
    time can be newer without refreshing its cached source content. A mixed batch
    is stored atomically, so its shortest applicable input deadline bounds it.
    """
    deadline = timestamp(permitted_until)
    checks = {item.checked_at for item in fetch.assertions}
    rows = db.execute("SELECT expires_at,payload FROM offer_fetch WHERE source=?", (fetch.source,))
    for expires_at, payload in rows:
        prior = decode_fetch(payload)
        if checks.intersection(item.checked_at for item in prior.assertions):
            deadline = min(deadline, expires_at)
    if deadline <= timestamp(now):
        raise ValueError("cached assertion retention expired; acquire a fresh source observation")
    return deadline
