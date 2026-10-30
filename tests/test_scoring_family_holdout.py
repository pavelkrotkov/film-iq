"""Source-family holdouts exclude derivatives and retain unknown exposure."""

from dataclasses import replace

from test_scoring_priority import ballot

from film_iq.scoring import score
from film_iq.scoring.policy import ScoringPolicy
from film_iq.scoring.snapshot import initialize, replay, save


def test_family_holdout_keeps_rank_ties_and_unknown_exposure(evidence_db):
    first = ballot("a", 2, source_family="training")
    tied = replace(first, film_id="other")
    held_out = ballot("b", 1, source_family="holdout")
    derivative = ballot("c", 1, derivative_of=("a",), source_family="aggregate")
    inputs = [first, tied, held_out, derivative]
    policy = ScoringPolicy(excluded_families=("holdout",))
    results = score(inputs, policy=policy)
    assert results[0].rank_score == results[1].rank_score
    assert results[0].contributing == (first,)
    assert set(results[0].excluded) == {held_out, derivative}
    initialize(evidence_db)
    assert replay(evidence_db, save(evidence_db, inputs, "now", policy=policy)) == results
    # A film with no supplied observations has unknown exposure, not a negative label.
    assert {result.film_id for result in results} == {"film", "other"}
