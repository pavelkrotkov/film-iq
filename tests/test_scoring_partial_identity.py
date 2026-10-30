"""A partial contributor-link rollout cannot manufacture independent support."""

from dataclasses import replace
from fractions import Fraction

import pytest
from test_scoring_priority import ballot

from film_iq.scoring import score
from film_iq.scoring.policy import ScoringPolicy
from film_iq.scoring.snapshot import initialize, save


def test_mixed_identity_coverage_preserves_reviewed_group_and_raw_identity():
    unknown = replace(ballot("a", 2), independence_group="reviewed-group")
    known = replace(ballot("b", 2), independence_group="reviewed-group", person_id="critic:1")
    result = score([unknown, known])[0]
    assert (result.independent_count, result.rank_score) == (1, Fraction(1, 2))
    assert (result.contributing, result.excluded) == ((unknown,), (known,))
    assert result.contributing[0].person_id is None
    assert score([known, unknown])[0] == result


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


def test_conflicting_group_person_mapping_requires_review_before_snapshot(evidence_db):
    first = ballot("a", 2, person_id="critic:1")
    conflict = replace(first, list_id="b", source_id="b", person_id="critic:2")
    initialize(evidence_db)
    with pytest.raises(ValueError, match="Conflicting people"):
        save(evidence_db, [first, conflict], "now")
    assert evidence_db.execute("SELECT count(*) FROM scoring_snapshot").fetchone() == (0,)
