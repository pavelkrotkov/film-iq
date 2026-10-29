"""SQLite initialization and versioned migrations."""

import sqlite3
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    """Open a local database with foreign keys and WAL enabled."""
    version = sqlite3.sqlite_version_info
    if not (
        (3, 44, 6) <= version < (3, 45) or (3, 50, 7) <= version < (3, 51) or version >= (3, 51, 3)
    ):
        raise RuntimeError(f"SQLite {sqlite3.sqlite_version} lacks the required WAL fix")
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    return db


def migrate(db: sqlite3.Connection) -> None:
    """Apply each migration atomically; refuse databases from a newer application."""
    if db.in_transaction:
        raise ValueError("finish the current transaction before migrating")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > 2:
        raise ValueError(f"unsupported schema version: {version}")
    if version == 0:
        try:
            db.executescript(
                "BEGIN;\n"
                + (Path(__file__).with_name("001.sql")).read_text()
                + "\nPRAGMA user_version = 1;\nCOMMIT;"
            )
        except sqlite3.Error:
            db.rollback()
            raise
    if version < 2:
        try:
            db.executescript(
                "BEGIN;\n"
                + (Path(__file__).with_name("002.sql")).read_text()
                + "\nPRAGMA user_version = 2;\nCOMMIT;"
            )
        except sqlite3.Error:
            db.rollback()
            raise
