import pytest

from film_iq.identity import Candidate, Observation, resolve, review


def test_resolution_and_reversible_review() -> None:
    short = Candidate(1, ("Synthetic Short", "Titre Alternatif"), "A Director", 2020, "tt001")
    remake = Candidate(2, ("Synthetic Short",), "B Director", 2020, "tt002")
    duplicate = Candidate(3, ("Synthetic Short",), "A Director", 2020, "tt003")
    candidates = (short, remake, duplicate)

    raw = Observation("Titre Alternatif", "A Director", 2020)
    decision = resolve(raw, candidates)
    assert decision.match == 1
    assert decision.candidates == (1, 2, 3)
    assert resolve(Observation("Wrong title", tmdb_id=2), candidates).match == 2
    assert resolve(Observation("Wrong title", imdb_id="tt001"), candidates).match == 1
    assert resolve(Observation("Synthetic Short", "A Director", 2020), candidates).match is None
    assert resolve(Observation("Synthetic Short", year=2020), candidates).match is None
    assert (
        resolve(Observation("Synthetic Short", tmdb_id=1, imdb_id="tt002"), candidates).match
        is None
    )
    assert resolve(Observation("Unknown", tmdb_id=999), candidates).match is None

    corrected = review((decision,), 2, "reviewer", "The source refers to another film")
    assert corrected[0] == decision
    assert corrected[-1].observation == raw
    assert corrected[-1].match == 2
    assert review(corrected, 1, "reviewer", "Reinstated after checking")[-1].match == 1
    with pytest.raises(ValueError):
        review(corrected, 999, "reviewer", "Not a recorded candidate")
    with pytest.raises(ValueError):
        review(corrected, None, "", "Missing reviewer")


def test_persist_unresolved_and_reverse_against_draft_contract() -> None:
    import sqlite3
    from dataclasses import replace
    from pathlib import Path

    from film_iq.identity import load, save

    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")
    root = Path(__file__).resolve().parents[1]
    migration = root / "src/film_iq/storage/001.sql"
    db.executescript(migration.read_text())
    db.executescript("""
        INSERT INTO source VALUES ('s','Source','poll','original','url',NULL,NULL,
            'public','metadata','none','source',NULL);
        INSERT INTO source_run VALUES ('run','s','now',NULL,'success','v1',NULL,NULL);
        INSERT INTO source_document VALUES ('doc','s','url','hash','now',NULL,'success','metadata');
        INSERT INTO published_list VALUES ('list','s','edition',NULL,'all',NULL,'ranked','complete','original');
        INSERT INTO extraction_revision VALUES ('rev','s','doc','run','v1','valid','accepted');
        INSERT INTO extraction_revision VALUES ('rev2','s','doc','run','v2','valid','accepted');
        INSERT INTO list_entry VALUES ('entry','s','list','one');
        INSERT INTO list_entry VALUES ('other','s','list','two');
        INSERT INTO entry_observation VALUES ('entry','s','rev','A','context',NULL,2020,'Director',1,1,NULL,'#1','accepted');
        INSERT INTO entry_observation VALUES ('entry','s','rev2','Corrected','context',NULL,2020,'Director',1,1,NULL,'#1','accepted');
        INSERT INTO film_index (id, tmdb_id) VALUES (42, 1), (43, 2);
    """)
    original = resolve(
        Observation("A", "Director", 2020),
        (
            Candidate(1, ("A",), "Director", 2020),
            Candidate(2, ("A",), "Director", 2020),
        ),
    )
    first = save(db, "entry", "rev", original)
    assert load(db, first) == (original, None)
    corrected = review((original,), 2, "reviewer", "Checked source")[1]
    second = save(db, "entry", "rev2", corrected, first)
    assert load(db, second) == (corrected, first)
    assert db.execute("SELECT film_id FROM match_decision WHERE id = ?", (second,)).fetchone() == (
        43,
    )
    assert db.execute("SELECT revision_id FROM match_decision ORDER BY rowid").fetchall() == [
        ("rev",),
        ("rev2",),
    ]
    assert db.execute(
        "SELECT raw_title FROM entry_observation ORDER BY revision_id"
    ).fetchall() == [("A",), ("Corrected",)]
    with pytest.raises(ValueError, match="same entry"):
        save(db, "other", "rev", corrected, first)
    with pytest.raises(ValueError, match="film_index"):
        save(db, "entry", "rev", replace(corrected, match=999))
    for entry_id, revision_id in [("entry", "missing"), ("other", "rev")]:
        with pytest.raises(sqlite3.IntegrityError):
            save(db, entry_id, revision_id, original)
