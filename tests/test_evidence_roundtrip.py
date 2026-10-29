import sqlite3

import pytest

from film_iq.storage import connect


def test_migration_and_evidence_roundtrip(evidence_db, tmp_path):
    db = evidence_db
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
        "INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
            None,
            "002",
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
            "INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
                None,
                None,
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
    _check_match_decisions_and_reviews(db)
    db.commit()
    db.close()
    db = connect(tmp_path / "evidence.db")
    assert db.execute(
        "SELECT raw_title, rank, tie FROM entry_observation ORDER BY revision_id"
    ).fetchall() == [("Unchanged title", 1, "tie-a"), ("Corrected", 1, "tie-a")]
    assert db.execute(
        "SELECT source_id, list_id, entry_id, revision_id, raw_imdb_id, raw_tmdb_id "
        "FROM entry_observation ORDER BY revision_id"
    ).fetchall() == [
        ("s", "list", "entry", "rev", "tt0000001", "001"),
        ("s", "list", "entry", "rev2", None, "002"),
    ]
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO list_entry VALUES (?,?,?,?)", ("bad", "missing", "list", "bad"))
    db.close()


def _check_match_decisions_and_reviews(db):
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
