"""FilmIQ's reversible recommendation state; personal history stays in Movary."""

import sqlite3
from contextlib import closing
from pathlib import Path

from film_iq.storage import connect

STATES = {"discover": "Discover", "saved": "Saved", "dismissed": "Dismissed"}


def read(database: Path) -> dict[int, str]:
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        return dict(db.execute("SELECT tmdb_id,state FROM recommendation_disposition"))


def change(database: Path, tmdb_id: int, state: str) -> None:
    if state not in STATES:
        raise ValueError("Unknown recommendation action")
    with closing(connect(database)) as db, db:
        if state == "discover":
            db.execute("DELETE FROM recommendation_disposition WHERE tmdb_id=?", (tmdb_id,))
        else:
            db.execute(
                "INSERT INTO recommendation_disposition VALUES (?,?) ON CONFLICT(tmdb_id) "
                "DO UPDATE SET state=excluded.state WHERE state!=excluded.state",
                (tmdb_id, state),
            )


def attach(items: list[dict], states: dict[int, str]) -> list[dict]:
    return [{**item, "disposition": states.get(item["tmdb_id"], "discover")} for item in items]
