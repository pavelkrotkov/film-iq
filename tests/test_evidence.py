import sqlite3
from pathlib import Path

import pytest

from film_iq.domain import Observation
from film_iq.storage import connect, migrate


def test_upgrade_preserves_existing_observation(tmp_path):
    db = sqlite3.connect(tmp_path / "old.db")
    schema = Path(__file__).parents[1] / "src/film_iq/storage/001.sql"
    db.executescript(schema.read_text() + "\nPRAGMA user_version = 1;")
    db.execute(
        "INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("e", "s", "l", "r", "title", "", None, None, None, None, None, None, "#1", "pending"),
    )
    db.commit()
    migrate(db)
    assert db.execute(
        "SELECT raw_title, raw_imdb_id, raw_tmdb_id FROM entry_observation"
    ).fetchone() == ("title", None, None)
    db.close()


def test_rejects_unpatched_sqlite(monkeypatch, tmp_path):
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 45, 1))
    with pytest.raises(RuntimeError, match="WAL fix"):
        connect(tmp_path / "evidence.db")


def test_observation_validation_and_rights(tmp_path):
    with pytest.raises(ValueError):
        Observation("s", "l", "e", "r", "v", "", "", "#1")
    with pytest.raises(ValueError):
        Observation("s", "l", "e", "r", "v", "title", "", "#1", 0)
    db = connect(tmp_path / "evidence.db")
    migrate(db)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO source (id, name, family, independence_group, url, country, cadence, access_policy, retention_policy, redistribution_policy, attribution, health) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
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
    db.execute("PRAGMA user_version = 8")
    with pytest.raises(ValueError, match="unsupported"):
        migrate(db)
    db.close()
