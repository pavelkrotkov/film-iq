"""A partial contributor-link rollout cannot manufacture independent support."""

from dataclasses import replace
from fractions import Fraction

from test_scoring_priority import ballot

from film_iq.scoring import score
from film_iq.scoring.policy import ScoringPolicy


def test_partial_group_overlap_still_deduplicates_cross_publication_person():
    unknown = replace(ballot("a", 8), independence_group="reviewed-group")
    known = replace(ballot("b", 1), independence_group="reviewed-group", person_id="critic:1")
    other = ballot("c", 1, person_id="critic:1")
    result = score([other, known, unknown], policy=ScoringPolicy(source_priority=("a", "c", "b")))[
        0
    ]
    assert (result.independent_count, result.rank_score) == (1, Fraction(1, 8))
    assert result.contributing == (unknown,)
    assert set(result.excluded) == {known, other}
