import sqlite3

import pytest


def test_current_match_requires_accepted_decision_for_observation_and_film(evidence_db):
    db = evidence_db
    db.executemany("INSERT INTO film_index (id) VALUES (?)", [(1,), (2,)])
    insert = "INSERT INTO match_decision (id, entry_id, revision_id, film_id, candidates, method, version, decision, decided_at) VALUES (?, 'entry', 'rev', ?, '[]', 'manual', 'v1', ?, 'now')"
    db.executemany(
        insert,
        [
            ("accepted", 1, "accepted"),
            ("other", 2, "accepted"),
            ("pending", 1, "pending"),
            ("no-film", None, "accepted"),
        ],
    )
    current = "INSERT INTO current_match (entry_id, revision_id, decision_id, film_id) VALUES (?, ?, ?, ?)"
    for values in [
        ("entry", "rev", "pending", 1),
        ("entry", "rev", "no-film", None),
        ("entry", "rev", "accepted", 2),
        ("entry", "missing", "accepted", 1),
    ]:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(current, values)
    db.execute(current, ("entry", "rev", "accepted", 1))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(current, ("entry", "rev", "other", 2))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE match_decision SET decision = 'rejected' WHERE id = 'accepted'")
    db.execute("UPDATE current_match SET decision_id = 'other', film_id = 2")
    assert db.execute("SELECT decision_id, film_id FROM current_match").fetchone() == ("other", 2)
    assert db.execute("SELECT count(*) FROM match_decision").fetchone() == (4,)
