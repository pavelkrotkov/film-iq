"""Current matches are a projection of immutable decisions, not the source evidence.

Automatic replay must preserve a critic's correction or unresolved decision.
A rejected projection update must also roll back its newly appended decision.
"""

import sqlite3
from dataclasses import replace

import pytest

from film_iq.identity import Candidate, Observation, load, resolve, review, save


@pytest.fixture
def automatic_case(evidence_db):
    evidence_db.execute("INSERT INTO film_index (id, tmdb_id) VALUES (42, 1), (43, 2)")
    source = Observation("Unchanged title", tmdb_id=1, imdb_id="tt0000001")
    candidates = (Candidate(1, ("A",), imdb_id="tt0000001"), Candidate(2, ("B",)))
    return evidence_db, source, candidates


def _current(db):
    return db.execute("SELECT decision_id, film_id FROM current_match").fetchone()


@pytest.mark.parametrize("reviewed_match", [2, None])
def test_changed_automatic_evidence_preserves_review(automatic_case, reviewed_match):
    db, source, candidates = automatic_case
    original = resolve(source, candidates)
    first = save(db, "entry", "rev", original)
    reviewed = review((original,), reviewed_match, "critic", "Checked")[-1]
    reviewed_id = save(db, "entry", "rev", reviewed, first)
    expected = (reviewed_id, 43) if reviewed_match else None
    for updated in (
        tuple(reversed(candidates)),
        (replace(candidates[0], titles=("New",)), candidates[1]),
    ):
        automatic = resolve(source, updated)
        automatic_id = save(db, "entry", "rev", automatic)
        assert load(db, automatic_id) == (automatic, None)
        assert _current(db) == expected
    correction = review((reviewed,), 1, "critic", "Rechecked")[-1]
    correction_id = save(db, "entry", "rev", correction, reviewed_id)
    assert _current(db) == (
        correction_id,
        42,
    )
    assert load(db, correction_id) == (correction, reviewed_id)


def test_current_match_corrections_and_atomicity(automatic_case):
    db, source, candidates = automatic_case
    accepted = resolve(source, candidates)
    first = save(db, "entry", "rev", accepted)
    assert _current(db) == (first, 42)
    corrected = review((accepted,), 2, "critic", "Checked")[1]
    second = save(db, "entry", "rev", corrected, first)
    assert _current(db) == (second, 43)
    _check_replay(db, accepted, first, (second, 43))
    unresolved = review((corrected,), None, "critic", "Uncertain")[1]
    third = save(db, "entry", "rev", unresolved, second)
    assert _current(db) is None
    _check_replay(db, accepted, first, None)
    assert load(db, third) == (unresolved, second)
    assert load(db, first) == (accepted, None)
    assert db.execute(
        "SELECT raw_title, raw_context, locator, raw_tmdb_id, raw_imdb_id FROM entry_observation"
    ).fetchone() == ("Unchanged title", "context", "#1", "001", "tt0000001")
    _check_atomicity(db, corrected, third)


def _check_replay(db, accepted, first, expected):
    # A replay must preserve both the review outcome and the decision history.
    assert save(db, "entry", "rev", accepted) == first
    assert _current(db) == expected
    assert db.execute("SELECT count(*) FROM match_decision").fetchone() == (2 if expected else 3,)


def _check_atomicity(db, corrected, third):
    db.execute(
        "CREATE TRIGGER reject_current BEFORE INSERT ON current_match BEGIN SELECT RAISE(ABORT, 'blocked'); END"
    )
    with pytest.raises(sqlite3.IntegrityError, match="blocked"):
        save(db, "entry", "rev", corrected, third)
    assert _current(db) is None
    assert db.execute("SELECT count(*) FROM match_decision").fetchone() == (3,)
    db.rollback()
    assert db.execute("SELECT count(*) FROM match_decision").fetchone() == (0,)


@pytest.mark.parametrize("raw_id", ["not-an-id", "1.5", "1x"])
def test_malformed_source_id_allows_only_unresolved_review(evidence_db, raw_id):
    db = evidence_db
    db.execute("UPDATE entry_observation SET raw_tmdb_id = ?", (raw_id,))
    db.execute("INSERT INTO film_index (id, tmdb_id) VALUES (42, 1)")
    source = Observation("Unchanged title", imdb_id="tt0000001")
    candidate = Candidate(1, ("Unchanged title",), imdb_id="tt0000001")
    accepted = resolve(source, (candidate,))
    assert accepted.match == 1
    with pytest.raises(ValueError, match="requires an unresolved decision"):
        save(db, "entry", "rev", accepted)
    unresolved = review((accepted,), None, "reviewer", "Malformed source ID")[-1]
    decision_id = save(db, "entry", "rev", unresolved)
    assert load(db, decision_id) == (unresolved, None)
    assert db.execute("SELECT raw_tmdb_id FROM entry_observation").fetchone() == (raw_id,)
    assert db.execute("SELECT decision, film_id FROM match_decision").fetchone() == (
        "unresolved",
        None,
    )
    assert db.execute("SELECT count(*) FROM current_match").fetchone() == (0,)
