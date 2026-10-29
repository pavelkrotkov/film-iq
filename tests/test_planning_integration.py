from dataclasses import replace
from datetime import date

import pytest

from film_iq.planning.integration import UTILITY_VERSION, planner_film
from film_iq.planning.models import Access
from film_iq.planning.monthly import compare
from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence


def test_current_evidence_to_planner(evidence_db):
    db = evidence_db
    db.execute("UPDATE source SET independence_verification = 'verified'")
    db.execute(
        "UPDATE published_list SET lineage_verification = 'verified', lineage_kind = 'original'"
    )
    db.execute("INSERT INTO film_index (id, tmdb_id) VALUES (42, 1234)")
    db.execute(
        "INSERT INTO match_decision VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("match", "entry", "rev", 42, "[]", "manual", "1", None, None, "accepted", "now", None),
    )
    db.execute("INSERT INTO current_extraction (list_id, revision_id) VALUES ('list', 'rev')")
    db.execute(
        "INSERT INTO current_match (entry_id, revision_id, decision_id, film_id) VALUES ('entry', 'rev', 'match', 42)"
    )
    result = score(load_evidence(db))[0]
    film = planner_film(db, result, "Film", 90, False)
    assert UTILITY_VERSION == "independent-count-additive-v1"
    assert (film.id, film.score) == (1234, 1.0)
    plans = compare(
        [film],
        [Access(1234, 1, "subscription", "confirmed")],
        {1},
        [date(2026, 11, 1)],
        90,
        1,
        0,
        {},
    )
    assert plans[0].utility == 1.0
    assert plans[0].choices[0].film == film
    for invalid in (
        replace(result, film_id="999"),
        replace(result, version="unknown"),
        replace(result, independent_count=0),
    ):
        with pytest.raises(ValueError):
            planner_film(db, invalid, "Film", 90, False)
    for tmdb_id in (None, 0, -1, "unknown"):
        db.execute("UPDATE film_index SET tmdb_id = ? WHERE id = 42", (tmdb_id,))
        with pytest.raises(ValueError, match="crosswalk"):
            planner_film(db, result, "Film", 90, False)
