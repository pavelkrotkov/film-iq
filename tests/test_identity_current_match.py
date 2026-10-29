import pytest

from film_iq.identity import Candidate, Observation, resolve, review


def test_current_match_corrections_and_atomicity(evidence_db):
    from film_iq.identity import load, save

    db = evidence_db
    db.execute("INSERT INTO film_index (id, tmdb_id) VALUES (42, 1), (43, 2)")
    source = Observation("Unchanged title", tmdb_id=1, imdb_id="tt0000001")
    candidates = (Candidate(1, ("A",), imdb_id="tt0000001"), Candidate(2, ("B",)))
    accepted = resolve(source, candidates)
    first = save(db, "entry", "rev", accepted)
    current = lambda: db.execute(  # noqa: E731
        "SELECT decision_id, film_id FROM current_match WHERE entry_id = 'entry' AND revision_id = 'rev'"
    ).fetchone()
    assert current() == (first, 42)
    corrected = review((accepted,), 2, "critic", "Checked")[1]
    second = save(db, "entry", "rev", corrected, first)
    assert current() == (second, 43)
    unresolved = review((corrected,), None, "critic", "Uncertain")[1]
    third = save(db, "entry", "rev", unresolved, second)
    assert current() is None
    assert load(db, third) == (unresolved, second)
    assert load(db, first) == (accepted, None)
    assert db.execute(
        "SELECT raw_title, raw_context, locator, raw_tmdb_id, raw_imdb_id FROM entry_observation"
    ).fetchone() == ("Unchanged title", "context", "#1", "001", "tt0000001")
    _check_atomicity(db, corrected, third, current)


def _check_atomicity(db, corrected, third, current):
    import sqlite3

    from film_iq.identity import save

    db.execute(
        "CREATE TRIGGER reject_current BEFORE INSERT ON current_match BEGIN SELECT RAISE(ABORT, 'blocked'); END"
    )
    with pytest.raises(sqlite3.IntegrityError, match="blocked"):
        save(db, "entry", "rev", corrected, third)
    assert current() is None
    assert db.execute("SELECT count(*) FROM match_decision").fetchone() == (3,)
    db.rollback()
    assert db.execute("SELECT count(*) FROM match_decision").fetchone() == (0,)
