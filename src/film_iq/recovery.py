"""Private online SQLite copies into new files; never overwrite a running database."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path


def validate(db: sqlite3.Connection) -> None:
    """Reject corrupt or referentially inconsistent backup/restore candidates."""
    if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("database integrity check failed")
    if db.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("database foreign key check failed")


def backup(db: sqlite3.Connection, destination: Path) -> None:
    """Copy committed WAL state with SQLite's online backup API into a private file."""
    if db.in_transaction:
        raise ValueError("commit or roll back before backup")
    validate(db)
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(destination)) as target:
            db.backup(target)
            validate(target)
    except (OSError, ValueError, sqlite3.Error):
        destination.unlink()
        raise


def restore(source: Path, destination: Path) -> None:
    """Restore offline to a new path; the operator validates before switching services."""
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as original:
        backup(original, destination)
