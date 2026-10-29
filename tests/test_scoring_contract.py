import sqlite3
from pathlib import Path

import pytest

from film_iq.storage import migrate


def test_upgrade_preserves_unverified_metadata(tmp_path):
    db = sqlite3.connect(tmp_path / "v2.db")
    storage = Path(__file__).parents[1] / "src/film_iq/storage"
    db.executescript((storage / "001.sql").read_text() + (storage / "002.sql").read_text())
    db.execute(
        "INSERT INTO source VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "s",
            "Source",
            "poll",
            "shared group",
            "url",
            None,
            None,
            "public",
            "metadata",
            "none",
            "credit",
            None,
        ),
    )
    db.execute(
        "INSERT INTO published_list VALUES (?,?,?,?,?,?,?,?,?)",
        (
            "l",
            "s",
            "2025",
            None,
            "eligible",
            None,
            "ranked",
            "complete",
            "derived from poll",
        ),
    )
    db.execute("PRAGMA user_version = 2")
    db.commit()
    migrate(db)
    assert db.execute(
        "SELECT independence_group, independence_verification FROM source"
    ).fetchone() == (
        "shared group",
        "unknown",
    )
    assert db.execute("SELECT lineage, lineage_verification FROM published_list").fetchone() == (
        "derived from poll",
        "unknown",
    )
    for table, column in [
        ("source", "independence_verification"),
        ("published_list", "lineage_verification"),
    ]:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(f"UPDATE {table} SET {column} = 'independent'")
        db.execute(f"UPDATE {table} SET {column} = 'verified'")
        db.execute(f"UPDATE {table} SET {column} = 'disputed'")
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    db.close()


def test_lineage_kind_is_independent_of_text_and_verification(evidence_db):
    db = evidence_db
    db.execute("UPDATE published_list SET lineage_verification = 'verified'")
    assert db.execute(
        "SELECT lineage, lineage_verification, lineage_kind FROM published_list"
    ).fetchone() == ("original", "verified", "unknown")
    for kind in ("original", "derivative", "unknown"):
        db.execute("UPDATE published_list SET lineage_kind = ?", (kind,))
        assert db.execute("SELECT lineage_verification FROM published_list").fetchone() == (
            "verified",
        )
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE published_list SET lineage_kind = 'independent'")
