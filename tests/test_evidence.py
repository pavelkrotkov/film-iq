import sqlite3

import pytest

from film_iq.domain import Observation
from film_iq.storage import connect, migrate


def test_rejects_unpatched_sqlite(monkeypatch, tmp_path):
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 45, 1))
    with pytest.raises(RuntimeError, match="WAL fix"):
        connect(tmp_path / "evidence.db")


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
        "INSERT INTO extraction_revision VALUES (?,?,?,?,?,?,?,?)",
        (
            "rev",
            "s",
            "list",
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
        observation.edition_id,
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
    db.execute("INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO list_entry VALUES (?,?,?,?)", ("other", "s", "list", "item-1"))
    db.execute(
        "INSERT INTO extraction_revision VALUES (?,?,?,?,?,?,?,?)",
        (
            "rev2",
            "s",
            "list",
            "doc",
            "run",
            "v2",
            "valid",
            "accepted",
        ),
    )
    db.execute(
        "INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "entry",
            "s",
            "list",
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
    db.execute(
        "INSERT INTO current_extraction (list_id, revision_id) VALUES (?,?)", ("list", "rev")
    )
    db.execute("UPDATE current_extraction SET revision_id = ? WHERE list_id = ?", ("rev2", "list"))
    assert db.execute(
        "SELECT o.raw_title FROM current_extraction c JOIN entry_observation o "
        "ON o.list_id = c.list_id AND o.revision_id = c.revision_id"
    ).fetchall() == [("Corrected",)]
    db.execute(
        "INSERT INTO published_list VALUES (?,?,?,?,?,?,?,?,?)",
        ("list2", "s", "2024", None, "eligible", None, "ranked", "complete", "original"),
    )
    db.execute("INSERT INTO list_entry VALUES (?,?,?,?)", ("other", "s", "list2", "item-2"))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "other",
                "s",
                "list2",
                "rev",
                "Wrong list",
                "",
                None,
                None,
                None,
                1,
                1,
                None,
                "#1",
                "accepted",
            ),
        )
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO current_extraction (list_id, revision_id) VALUES (?,?)", ("list2", "rev")
        )
    db.execute(
        "INSERT INTO extraction_revision VALUES (?,?,?,?,?,?,?,?)",
        ("pending", "s", "list2", "doc", "run", "v1", "valid", "pending"),
    )
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO current_extraction (list_id, revision_id) VALUES (?,?)",
            ("list2", "pending"),
        )
    decision = "INSERT INTO match_decision (id, entry_id, revision_id, candidates, method, version, decision, decided_at) VALUES (?,?,?,?,?,?,?,?)"
    db.execute(decision, ("match", "entry", "rev", "[]", "manual", "v1", "accepted", "now"))
    for entry_id, revision_id in [("entry", None), ("entry", "missing"), ("other", "rev")]:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                decision, ("bad", entry_id, revision_id, "[]", "manual", "v1", "accepted", "now")
            )
    review = "INSERT INTO review (id, entry_id, revision_id, reason, status, created_at) VALUES (?,?,?,?,?,?)"
    for review_id, entry_id, revision_id in [
        ("paired", "entry", "rev"),
        ("revision-only", None, "rev"),
        ("entry-only", "other", None),
    ]:
        db.execute(review, (review_id, entry_id, revision_id, "reason", "open", "now"))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(review, ("wrong-pair", "other", "rev", "reason", "open", "now"))
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


def test_wal_backup_and_restore(tmp_path):
    db = connect(tmp_path / "live.db")
    migrate(db)
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
            "public",
            "metadata",
            "none",
            "cite",
            None,
        ),
    )
    db.commit()
    with sqlite3.connect(tmp_path / "backup.db") as backup:
        db.backup(backup)
    db.execute("DELETE FROM source")
    db.commit()
    db.close()
    with (
        sqlite3.connect(tmp_path / "backup.db") as backup,
        sqlite3.connect(tmp_path / "restored.db") as restored,
    ):
        backup.backup(restored)
    restored = connect(tmp_path / "restored.db")
    assert restored.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    assert restored.execute("PRAGMA user_version").fetchone() == (1,)
    assert restored.execute("SELECT id FROM source").fetchall() == [("s",)]
    restored.close()
