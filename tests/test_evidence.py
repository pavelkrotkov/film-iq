import sqlite3

import pytest

from film_iq.domain import Observation
from film_iq.storage import connect, migrate


def test_migration_and_evidence_roundtrip(tmp_path):
    db = connect(tmp_path / "evidence.db")
    migrate(db)
    migrate(db)
    assert db.execute("PRAGMA user_version").fetchone() == (1,)
    assert db.execute("PRAGMA foreign_keys").fetchone() == (1,)
    assert db.execute("PRAGMA journal_mode").fetchone() == ("wal",)
    db.execute(
        "INSERT INTO source VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "s",
            "Source",
            "poll",
            "original",
            "https://example.test",
            None,
            None,
            "public",
            "metadata only",
            "no copies",
            "cite source",
            None,
        ),
    )
    db.execute(
        "INSERT INTO source_run VALUES (?,?,?,?,?,?,?,?)",
        (
            "run",
            "s",
            "2026-01-01Z",
            None,
            "success",
            "v1",
            None,
            None,
        ),
    )
    db.execute(
        "INSERT INTO source_document VALUES (?,?,?,?,?,?,?,?)",
        (
            "doc",
            "s",
            "https://example.test/list",
            "hash",
            "2026-01-01Z",
            None,
            "success",
            "metadata only",
        ),
    )
    db.execute(
        "INSERT INTO published_list VALUES (?,?,?,?,?,?,?,?,?)",
        (
            "list",
            "s",
            "2025",
            "Critic",
            "released in 2025",
            "2025",
            "ranked",
            "partial",
            "original",
        ),
    )
    db.execute(
        "INSERT INTO extraction_revision VALUES (?,?,?,?,?,?,?)",
        (
            "rev",
            "s",
            "doc",
            "run",
            "v1",
            "valid",
            "accepted",
        ),
    )
    db.execute("INSERT INTO list_entry VALUES (?,?,?,?)", ("entry", "s", "list", "item-1"))
    observation = Observation(
        "s", "list", "entry", "run", "rev", "Unchanged title", "context", "#1", 1, "tie-a"
    )
    values = (
        observation.entry_id,
        observation.source_id,
        observation.revision_id,
        observation.raw_title,
        observation.raw_context,
        None,
        None,
        None,
        1,
        observation.rank,
        observation.tie,
        observation.locator,
        "accepted",
    )
    db.execute("INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO list_entry VALUES (?,?,?,?)", ("other", "s", "list", "item-1"))
    db.execute(
        "INSERT INTO extraction_revision VALUES (?,?,?,?,?,?,?)",
        (
            "rev2",
            "s",
            "doc",
            "run",
            "v2",
            "valid",
            "accepted",
        ),
    )
    db.execute(
        "INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "entry",
            "s",
            "rev2",
            "Corrected",
            "context",
            None,
            None,
            None,
            1,
            1,
            "tie-a",
            "#1",
            "accepted",
        ),
    )
    db.commit()
    db.close()
    db = connect(tmp_path / "evidence.db")
    assert db.execute(
        "SELECT raw_title, rank, tie FROM entry_observation ORDER BY revision_id"
    ).fetchall() == [("Unchanged title", 1, "tie-a"), ("Corrected", 1, "tie-a")]
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO list_entry VALUES (?,?,?,?)", ("bad", "missing", "list", "bad"))
    db.close()


def test_observation_validation_and_rights(tmp_path):
    with pytest.raises(ValueError):
        Observation("s", "l", "e", "r", "v", "", "", "#1")
    with pytest.raises(ValueError):
        Observation("s", "l", "e", "r", "v", "title", "", "#1", 0)
    db = connect(tmp_path / "evidence.db")
    migrate(db)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO source VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "s",
                "Source",
                "family",
                "group",
                "url",
                None,
                None,
                "",
                "unknown",
                "unknown",
                "unknown",
                None,
            ),
        )
    db.rollback()
    db.execute("PRAGMA user_version = 2")
    with pytest.raises(ValueError, match="unsupported"):
        migrate(db)
    db.close()
