from film_iq.storage import migrate


def test_schema_eight_upgrade_keeps_existing_evidence(evidence_db):
    db = evidence_db
    db.executescript("""
        DROP TABLE offer_event; DROP TABLE offer_current; DROP TABLE offer_fetch; DROP TABLE offer_purge; DROP TABLE offer_policy;
        DROP TABLE entry_ballot;
        DROP TABLE source_ballot;
        DROP INDEX list_entry_ballot_key;
        DROP TABLE acquisition_cursor;
        DROP TABLE acquisition_attempt;
        DROP TABLE acquisition_permission;
        PRAGMA user_version=8;
    """)
    migrate(db)
    migrate(db)
    assert db.execute("PRAGMA user_version").fetchone() == (10,)
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert db.execute("SELECT raw_title FROM entry_observation").fetchone() == ("Unchanged title",)
    assert db.execute("SELECT count(*) FROM acquisition_attempt").fetchone() == (0,)
