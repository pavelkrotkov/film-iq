import pytest

from film_iq.identity import Candidate, Observation, resolve, review


def test_persist_unresolved_and_reverse_against_migrated_schema() -> None:
    import sqlite3

    from film_iq.identity import load, save
    from film_iq.storage import migrate

    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")
    migrate(db)
    db.executescript("""
        INSERT INTO source (id,name,family,independence_group,url,country,cadence,access_policy,retention_policy,redistribution_policy,attribution,health) VALUES ('s','Source','poll','original','url',NULL,NULL,
            'public','metadata','none','source',NULL);
        INSERT INTO source_run VALUES ('run','s','now',NULL,'success','v1',NULL,NULL);
        INSERT INTO source_document VALUES ('doc','s','url','hash','now',NULL,'success','metadata');
        INSERT INTO published_list (id,source_id,edition,author,eligibility,period,rank_semantics,completeness,lineage) VALUES ('list','s','edition',NULL,'all',NULL,'ranked','complete','original');
        INSERT INTO extraction_revision VALUES ('rev','s','list','doc','run','v1','valid','accepted');
        INSERT INTO extraction_revision VALUES ('rev2','s','list','doc','run','v2','valid','accepted');
        INSERT INTO current_extraction (list_id, revision_id) VALUES ('list','rev');
        INSERT INTO list_entry VALUES ('entry','s','list','one');
        INSERT INTO list_entry VALUES ('other','s','list','two');
        INSERT INTO entry_observation VALUES ('entry','s','list','rev','A','context',NULL,2020,'Director',1,1,NULL,'#1','accepted',NULL,NULL);
        INSERT INTO entry_observation VALUES ('entry','s','list','rev2','Corrected','context',NULL,2020,'Director',1,1,NULL,'#1','accepted',NULL,NULL);
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
    db.execute("UPDATE current_extraction SET revision_id = 'rev2' WHERE list_id = 'list'")
    corrected = review((original,), 2, "reviewer", "Checked source")[1]
    with pytest.raises(ValueError, match="stored entry revision"):
        save(db, "entry", "rev2", corrected, first)
    second = save(db, "entry", "rev", corrected, first)
    assert load(db, second) == (corrected, first)
    assert db.execute("SELECT film_id FROM match_decision WHERE id = ?", (second,)).fetchone() == (
        43,
    )
    assert db.execute("SELECT revision_id FROM match_decision ORDER BY rowid").fetchall() == [
        ("rev",),
        ("rev",),
    ]
    assert db.execute(
        "SELECT raw_title FROM entry_observation ORDER BY revision_id"
    ).fetchall() == [("A",), ("Corrected",)]
    assert db.execute(
        "SELECT o.raw_title FROM current_extraction c JOIN entry_observation o "
        "ON o.list_id = c.list_id AND o.revision_id = c.revision_id"
    ).fetchone() == ("Corrected",)
    _check_rejected_decisions(db, original, corrected, first)
    _check_external_ids(db)


def _check_rejected_decisions(db, original, corrected, first):
    from dataclasses import replace

    from film_iq.identity import save

    with pytest.raises(ValueError, match="same entry"):
        save(db, "other", "rev", corrected, first)
    with pytest.raises(ValueError, match="film_index"):
        save(db, "entry", "rev", replace(corrected, match=999))
    with pytest.raises(ValueError, match="stored entry revision"):
        save(db, "other", "rev", original)
    with pytest.raises(ValueError, match="stored entry revision"):
        save(db, "entry", "missing", original)
    with pytest.raises(ValueError, match="stored entry revision"):
        save(db, "entry", "rev", replace(original, observation=Observation("A", "Other", 2020)))
    with pytest.raises(ValueError, match="stored entry revision"):
        save(db, "entry", "rev", replace(original, observation=Observation("A", "Director", 2021)))
    with pytest.raises(ValueError, match="stored entry revision"):
        save(
            db,
            "entry",
            "rev",
            replace(original, observation=Observation("A", "Director", 2020, tmdb_id=1)),
        )


def _check_external_ids(db):
    from film_iq.identity import load, save

    # Both source IDs must belong to the selected revision, including when a
    # numeric TMDB ID has leading zeroes in the raw extraction evidence.
    db.execute(
        "UPDATE entry_observation SET raw_tmdb_id = '001', raw_imdb_id = 'tt001' WHERE revision_id = 'rev'"
    )
    candidate = Candidate(1, ("A",), "Director", 2020, "tt001")
    observation = Observation("A", "Director", 2020, 1, "tt001")
    decision = resolve(observation, (candidate,))
    assert decision.match == 1
    assert load(db, save(db, "entry", "rev", decision)) == (decision, None)
    # A decision cannot omit or replace either ID that was present in the source.
    for other in (
        Observation("A", "Director", 2020, 2, "tt001"),
        Observation("A", "Director", 2020, 1, "tt002"),
        Observation("A", "Director", 2020),
        Observation("A", "Director", 2020, 1),
    ):
        with pytest.raises(ValueError, match="stored entry revision"):
            save(db, "entry", "rev", resolve(other, (candidate,)))
    # Single IDs and whitespace-only fields are valid when they match the source.
    for tmdb, imdb, source in [
        ("001", None, Observation("A", "Director", 2020, 1)),
        (None, "tt001", Observation("A", "Director", 2020, imdb_id="tt001")),
        (" ", " ", Observation("A", "Director", 2020)),
    ]:
        db.execute(
            "UPDATE entry_observation SET raw_tmdb_id = ?, raw_imdb_id = ? WHERE revision_id = 'rev'",
            (tmdb, imdb),
        )
        decision = resolve(source, (candidate,))
        assert load(db, save(db, "entry", "rev", decision)) == (decision, None)
