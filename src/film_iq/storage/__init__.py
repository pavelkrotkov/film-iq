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


def _check_schema_shape(db: sqlite3.Connection) -> None:
    # Early drafts reused version 1 without these provenance relationships.
    # Refuse them before any migration can alter the database.
    columns = {row[1] for row in db.execute("PRAGMA table_info(entry_observation)")}
    review_keys = db.execute("PRAGMA foreign_key_list(review)")
    if "list_id" not in columns or not any(row[2] == "entry_observation" for row in review_keys):
        raise ValueError("obsolete schema shape; see SQLite migration and recovery in README")


def migrate(db: sqlite3.Connection) -> None:
    """Apply each migration atomically; refuse databases from a newer application."""
    if db.in_transaction:
        raise ValueError("finish the current transaction before migrating")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > 7:
        raise ValueError(f"unsupported schema version: {version}")
    if version and version < 5:
        _check_schema_shape(db)
    for target in range(version + 1, 8):
        try:
            sql = Path(__file__).with_name(f"{target:03}.sql").read_text()
            # Commit the schema and its version together, or roll back both.
            db.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version = {target};\nCOMMIT;")
        except sqlite3.Error:
            db.rollback()
            raise
