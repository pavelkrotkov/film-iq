"""Online committed WAL backup and isolated recovery exercise."""

import sqlite3

import pytest

from film_iq.recovery import backup, restore, validate
from film_iq.storage import connect, migrate


def test_online_backup_restore_preserves_schema_and_refuses_overwrite(tmp_path):
    db = connect(tmp_path / "source.db")
    migrate(db)
    db.execute("CREATE TABLE recovery_probe (id INTEGER PRIMARY KEY, value TEXT)")
    db.execute("INSERT INTO recovery_probe VALUES (1, 'accepted revision marker')")
    with pytest.raises(ValueError, match="commit"):
        backup(db, tmp_path / "uncommitted.db")
    db.commit()
    backup(db, tmp_path / "backup.db")
    db.execute("UPDATE recovery_probe SET value = 'later'")
    db.commit()
    restore(tmp_path / "backup.db", tmp_path / "restored.db")
    with connect(tmp_path / "restored.db") as recovered:
        validate(recovered)
        assert recovered.execute("SELECT value FROM recovery_probe").fetchone() == (
            "accepted revision marker",
        )
        assert (
            recovered.execute("PRAGMA user_version").fetchone()
            == db.execute("PRAGMA user_version").fetchone()
        )
    with pytest.raises(FileExistsError):
        restore(tmp_path / "backup.db", tmp_path / "source.db")
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
