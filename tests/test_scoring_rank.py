from datetime import date
from fractions import Fraction

import pytest

from film_iq.scoring import Evidence, score


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
