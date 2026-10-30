from datetime import date
from fractions import Fraction

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
        Fraction(1, 5),
        1,
    )
    assert set(a.contributing) == {repeat, unranked}
    assert set(a.excluded) == {first, derivative}
    assert first.published == date(2024, 12, 1) and first.eligibility == "2024 releases"
    assert b.rank_score == Fraction(1, 2)
