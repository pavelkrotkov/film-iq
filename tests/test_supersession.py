import sqlite3

import pytest

from film_iq.storage import migrate


def test_supersession_stays_with_stable_entry_across_revisions(evidence_db):
    db = evidence_db
    db.execute("INSERT INTO list_entry VALUES ('other', 's', 'list', 'item-2')")
    db.execute(
        "INSERT INTO extraction_revision VALUES ('rev2', 's', 'list', 'doc', 'run', 'v2', 'valid', 'accepted')"
    )
    db.execute(
        "INSERT INTO entry_observation SELECT entry_id, source_id, list_id, 'rev2', raw_title, raw_context, original_title, listed_year, director, position, rank, tie, locator, extraction_decision, raw_imdb_id, raw_tmdb_id FROM entry_observation WHERE entry_id = 'entry'"
    )
    db.execute(
        "INSERT INTO entry_observation SELECT 'other', source_id, list_id, revision_id, raw_title, raw_context, original_title, listed_year, director, position, rank, tie, locator, extraction_decision, raw_imdb_id, raw_tmdb_id FROM entry_observation WHERE entry_id = 'entry' AND revision_id = 'rev'"
    )
    insert = "INSERT INTO match_decision (id, entry_id, revision_id, candidates, method, version, decision, decided_at, supersedes) VALUES (?, ?, ?, '[]', 'manual', 'v1', 'accepted', 'now', ?)"
    db.execute(insert, ("old", "entry", "rev", None))
    db.execute(insert, ("new", "entry", "rev2", "old"))
    db.execute(insert, ("other", "other", "rev", None))
    with pytest.raises(sqlite3.IntegrityError, match="another entry"):
        db.execute(insert, ("bad", "other", "rev", "old"))
    with pytest.raises(sqlite3.IntegrityError, match="another entry"):
        db.execute("UPDATE match_decision SET supersedes = 'other' WHERE id = 'new'")
    with pytest.raises(sqlite3.IntegrityError, match="another entry"):
        db.execute("UPDATE match_decision SET entry_id = 'other' WHERE id = 'old'")


def test_version_four_rejects_invalid_supersession_atomically(evidence_db):
    db = evidence_db
    db.execute("INSERT INTO list_entry VALUES ('other', 's', 'list', 'item-2')")
    db.execute(
        "INSERT INTO entry_observation SELECT 'other', source_id, list_id, revision_id, raw_title, raw_context, original_title, listed_year, director, position, rank, tie, locator, extraction_decision, raw_imdb_id, raw_tmdb_id FROM entry_observation"
    )
    db.execute("DROP TRIGGER match_supersedes_insert")
    db.execute("DROP TRIGGER match_supersedes_update")
    db.execute("DROP TABLE recognition_snapshot")
    db.execute("DROP TABLE entry_recognition")
    db.execute("DROP TABLE offer_event")
    db.execute("DROP TABLE offer_current")
    db.execute("DROP TABLE offer_fetch")
    db.execute("DROP TABLE offer_purge")
    db.execute("DROP TABLE offer_policy")
    db.execute("DROP TABLE entry_ballot")
    db.execute("DROP TABLE source_ballot")
    db.execute("DROP TABLE acquisition_cursor")
    db.execute("DROP TABLE acquisition_attempt")
    db.execute("DROP TABLE acquisition_permission")
    db.execute("DROP INDEX list_entry_ballot_key")
    db.execute("DROP TABLE extraction_audit")
    db.execute("DROP TABLE extraction_fingerprint")
    db.execute("DROP TABLE extraction_detail")
    db.execute("PRAGMA user_version = 4")
    db.execute(
        "INSERT INTO match_decision (id, entry_id, revision_id, candidates, method, version, decision, decided_at) VALUES ('old', 'entry', 'rev', '[]', 'manual', 'v1', 'accepted', 'now')"
    )
    db.execute(
        "INSERT INTO match_decision (id, entry_id, revision_id, candidates, method, version, decision, decided_at, supersedes) VALUES ('bad', 'other', 'rev', '[]', 'manual', 'v1', 'accepted', 'now', 'old')"
    )
    db.execute(
        "INSERT INTO match_decision (id, entry_id, revision_id, candidates, method, version, decision, decided_at, supersedes) VALUES ('valid', 'entry', 'rev', '[]', 'manual', 'v1', 'accepted', 'now', 'old')"
    )
    db.commit()
    with pytest.raises(sqlite3.IntegrityError):
        migrate(db)
    assert db.execute("PRAGMA user_version").fetchone() == (4,)
    assert db.execute("SELECT supersedes FROM match_decision WHERE id = 'bad'").fetchone() == (
        "old",
    )
    db.execute("UPDATE match_decision SET supersedes = NULL WHERE id = 'bad'")
    db.commit()
    migrate(db)
    assert db.execute("SELECT count(*) FROM match_decision").fetchone() == (3,)
    assert db.execute("SELECT supersedes FROM match_decision WHERE id = 'valid'").fetchone() == (
        "old",
    )
