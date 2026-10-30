import sqlite3

from film_iq.storage import connect, migrate


def test_wal_backup_and_restore(tmp_path):
    db = connect(tmp_path / "live.db")
    migrate(db)
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
    assert restored.execute("PRAGMA user_version").fetchone() == (9,)
    assert restored.execute("SELECT id FROM source").fetchall() == [("s",)]
    restored.close()
