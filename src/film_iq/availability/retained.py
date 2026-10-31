"""Guarded latest attempts plus comparison baselines, without inferring availability."""

import sqlite3
from datetime import datetime

from film_iq.availability.codec import decode_fetch, timestamp
from film_iq.availability.policies import policy_for, readable
from film_iq.availability.state import read_state


def retained_states(db: sqlite3.Connection, now: datetime) -> list[dict]:
    rows = db.execute(
        "WITH ranked AS (SELECT source,payload,row_number() OVER "
        "(PARTITION BY scope ORDER BY checked_at DESC,rowid DESC) AS position "
        "FROM offer_fetch WHERE checked_at<=? AND expires_at>?) "
        "SELECT source,payload FROM ranked WHERE position=1 ORDER BY source,payload",
        (timestamp(now), timestamp(now)),
    )
    return [
        {
            **read_state(db, decode_fetch(payload), now),
            "attribution": policy_for(db, source).attribution,
        }
        for source, payload in rows
        if readable(db, source, now)
    ]
