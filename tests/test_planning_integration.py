from datetime import date

import pytest

from film_iq.planning.integration import UTILITY_VERSION, planner_film
from film_iq.planning.models import Access
from film_iq.planning.monthly import compare
from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence


@pytest.fixture
def current_score(evidence_db):
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
    db.execute("INSERT INTO entry_recognition VALUES ('entry','rev','critic_selection','[]',NULL)")
    return score(load_evidence(db))[0]


def test_current_evidence_to_planner(evidence_db, current_score):
    film = planner_film(evidence_db, current_score, "Film", 90, False)
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
    assert_policy_assumptions(plans)
    empty_plans = compare([film], [], set(), [], 90, 1, 0, {})
    assert all(UTILITY_VERSION in plan.assumptions for plan in empty_plans)


def assert_policy_assumptions(plans):
    for plan in plans:
        assert UTILITY_VERSION in plan.assumptions
        assert "provisional, uncalibrated" in plan.assumptions
        assert "one point per independent endorsement" in plan.assumptions
        assert "rank and personal preference are ignored" in plan.assumptions
