"""C3 policy selection must never chase a critic's best rank."""

from dataclasses import replace
from fractions import Fraction

import pytest

from film_iq.scoring import Evidence, score
from film_iq.scoring.policy import ScoringPolicy


def ballot(source, rank, **kwargs):
    return Evidence(
        "film",
        source,
        "https://example.test/ballot",
        None,
        source,
        "2023",
        rank,
        source_id=source,
        **kwargs,
    )


def test_known_person_repeats_use_declared_source_then_window():
    preferred = ballot("first", 8, person_id="critic:1")
    better_rank = ballot("other", 1, person_id="critic:1")
    policy = ScoringPolicy(source_priority=("first", "other"))
    result = score([better_rank, preferred], policy=policy)[0]
    assert (result.independent_count, result.known_person_count, result.rank_score) == (
        1,
        1,
        Fraction(1, 8),
    )
    assert result.contributing == (preferred,) and result.excluded == (better_rank,)
    assert score([preferred, better_rank], policy=policy)[0] == result
    later = replace(preferred, list_id="later", eligibility="2024", rank=1)
    assert score([later, preferred], policy=ScoringPolicy(window_priority=("2023", "2024")))[
        0
    ].contributing == (preferred,)


def test_publisher_or_author_does_not_establish_known_people():
    entries = [
        ballot("publisher-a", 1, author="A Name"),
        ballot("publisher-b", None, author="A Name"),
    ]
    result = score(entries)[0]
    assert (
        result.independent_count,
        result.known_person_count,
        result.unknown_contributor_count,
    ) == (2, 0, 2)
    assert result.unranked_count == 1
    excluded = score(entries, policy=ScoringPolicy(excluded_sources=("publisher-a",)))[0]
    assert excluded.contributing == (entries[1],) and excluded.rank_score is None


def test_conflicting_same_ballot_rank_requires_review():
    item = ballot("source", 2)
    with pytest.raises(ValueError, match="Conflicting ranks"):
        score([item, replace(item, rank=1)])
    with pytest.raises(ValueError, match="person_id"):
        replace(item, person_id=" ")
