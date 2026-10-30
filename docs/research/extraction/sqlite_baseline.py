"""A small transactional SQLite baseline for the extraction experiment."""

import sqlite3
from collections.abc import Iterable


def load_batch(db: sqlite3.Connection, rows: Iterable[tuple[str, str | None]]) -> None:
    """Commit the entire batch, or roll it back if any row fails."""
    with db:
        db.executemany(
            """INSERT INTO observation (id, title) VALUES (?, ?)
               ON CONFLICT(id) DO UPDATE SET title = excluded.title
               WHERE observation.title != excluded.title""",
            rows,
        )
