from datetime import date
from fractions import Fraction

import pytest

from film_iq.scoring import VERSION, Evidence, score


def entry(film: str, list_id: str, group: str, rank: int | None, **kwargs) -> Evidence:
    return Evidence(
        film,
        list_id,
        f"https://example.org/{list_id}",
        date(2024, 12, 1),
        group,
        "2024 releases",
        rank,
        **kwargs,
    )


def test_independence_lineage_rank_and_reproducibility() -> None:
    first = entry("a", "original", "critic", 2)
    repeat = entry("a", "another-list", "critic", 5)
    derivative = entry("a", "aggregate", "aggregator", 1, derivative_of=("original",))
    unranked = entry("a", "unranked", "other", None)
    other = entry("b", "original", "critic", 2)
    evidence = [first, repeat, derivative, unranked, other, first]
    results = score(evidence)
    assert results == score(list(reversed(evidence)))
    a, b = results
    assert (a.film_id, a.version, a.independent_count, a.rank_score, a.unranked_count) == (
        "a",
        VERSION,
        2,
        Fraction(1, 2),
        1,
    )
    assert set(a.contributing) == {first, unranked}
    assert set(a.excluded) == {repeat, derivative}
    assert first.published == date(2024, 12, 1) and first.eligibility == "2024 releases"
    assert b.rank_score == Fraction(1, 2)


def test_rank_ties_unknowns_and_invalid_rank() -> None:
    entries = [entry("b", "x", "g", 2), entry("a", "x", "g", 2), entry("c", "x", "g", None)]
    a, b, c = score(entries)
    assert (a.film_id, b.film_id, c.film_id) == ("a", "b", "c")
    assert a.rank_score == b.rank_score == Fraction(1, 2)
    assert c.rank_score is None and c.unranked_count == 1
    only_derivative = score([entry("d", "aggregate", "g", 1, derivative_of=("missing",))])[0]
    assert only_derivative.independent_count == 0 and only_derivative.rank_score is None
    with pytest.raises(ValueError, match="rank"):
        entry("a", "x", "g", 0)
