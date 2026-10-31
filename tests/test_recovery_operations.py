"""Online committed WAL backup and isolated recovery exercise."""

import sqlite3

import pytest

from film_iq.recovery import backup, restore, validate
from film_iq.storage import connect, migrate


def test_online_backup_restore_preserves_schema_and_refuses_overwrite(evidence_db, tmp_path):
    db = evidence_db
    db.execute("UPDATE entry_observation SET raw_title='accepted revision marker'")
    db.executescript("""
        DROP TABLE recognition_snapshot; DROP TABLE entry_recognition;
        DROP TABLE offer_event; DROP TABLE offer_current; DROP TABLE offer_fetch;
        DROP TABLE offer_purge; DROP TABLE offer_policy; PRAGMA user_version=9;
    """)
    migrate(db)
    db.execute("UPDATE entry_observation SET raw_title=raw_title")
    with pytest.raises(ValueError, match="commit"):
        backup(db, tmp_path / "uncommitted.db")
    db.commit()
    backup(db, tmp_path / "backup.db")
    db.execute("UPDATE entry_observation SET raw_title='later'")
    db.commit()
    restore(tmp_path / "backup.db", tmp_path / "restored.db")
    with connect(tmp_path / "restored.db") as recovered:
        validate(recovered)
        assert recovered.execute("SELECT raw_title FROM entry_observation").fetchone() == (
            "accepted revision marker",
        )
        assert recovered.execute("PRAGMA user_version").fetchone() == (11,)
    with pytest.raises(FileExistsError):
        restore(tmp_path / "backup.db", tmp_path / "evidence.db")
    assert (tmp_path / "backup.db").stat().st_mode & 0o777 == 0o600
    db.close()


def test_invalid_foreign_keys_block_copy(tmp_path):
    with sqlite3.connect(":memory:") as db:
        db.executescript(
            "CREATE TABLE p(id PRIMARY KEY); CREATE TABLE c(p REFERENCES p(id)); INSERT INTO c VALUES(1);"
        )
        with pytest.raises(ValueError, match="foreign key"):
            backup(db, tmp_path / "invalid.db")
    assert not (tmp_path / "invalid.db").exists()
