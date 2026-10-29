"""Pure, provisional public-evidence baselines; no personal preference model.

Each input is one accepted observation for an identified film. Independence groups
must already account for shared critics and source families; derivative observations
are retained for explanation but never contribute. Rank is a true published rank,
not display order. A missing rank is unknown, not a zero score.
"""

from dataclasses import dataclass
from datetime import date
from fractions import Fraction

VERSION = "independent-reciprocal-rank-v1"


@dataclass(frozen=True)
class Evidence:
    film_id: str
    list_id: str
    url: str
    published: date | None
    independence_group: str
    eligibility: str
    rank: int | None = None
    derivative_of: tuple[str, ...] = ()
    entry_id: str | None = None
    revision_id: str | None = None
    match_decision_id: str | None = None

    def __post_init__(self) -> None:
        if self.rank is not None and self.rank < 1:
            raise ValueError("rank must be positive or unknown")


@dataclass(frozen=True)
class Score:
    film_id: str
    version: str
    independent_count: int
    rank_score: Fraction | None
    contributing: tuple[Evidence, ...]
    excluded: tuple[Evidence, ...]
    unranked_count: int


def score(evidence: list[Evidence]) -> tuple[Score, ...]:
    """Rank films by independent count, then reciprocal-rank sum, then ID.

    Within a group the best known rank contributes; ties use list ID and the
    remaining fields for a reproducible choice. Unranked endorsements count,
    but add no known rank contribution; ``unranked_count`` exposes that limit.
    Duplicate observations and derivatives never add endorsements.
    """
    films: dict[str, set[Evidence]] = {}
    for item in evidence:
        films.setdefault(item.film_id, set()).add(item)
    results = [_score_film(film_id, items) for film_id, items in films.items()]
    return tuple(
        sorted(
            results, key=lambda s: (-s.independent_count, -(s.rank_score or Fraction()), s.film_id)
        )
    )


def _score_film(film_id: str, items: set[Evidence]) -> Score:
    chosen: dict[str, Evidence] = {}
    originals = (item for item in items if not item.derivative_of)
    for item in sorted(originals, key=lambda e: (e.rank or float("inf"), _evidence_key(e))):
        chosen.setdefault(item.independence_group, item)
    contributing = tuple(sorted(chosen.values(), key=_evidence_key))
    return Score(
        film_id=film_id,
        version=VERSION,
        independent_count=len(contributing),
        rank_score=_rank_score(contributing),
        contributing=contributing,
        excluded=tuple(sorted(items - set(contributing), key=_evidence_key)),
        unranked_count=sum(item.rank is None for item in contributing),
    )


def _evidence_key(item: Evidence) -> tuple:
    return (
        item.film_id,
        item.list_id,
        item.url,
        item.published.isoformat() if item.published else "",
        item.independence_group,
        item.eligibility,
        item.rank or 0,
        item.derivative_of,
        (item.entry_id is not None, item.entry_id or ""),
        (item.revision_id is not None, item.revision_id or ""),
        (item.match_decision_id is not None, item.match_decision_id or ""),
    )


def _rank_score(items: tuple[Evidence, ...]) -> Fraction | None:
    ranks = [Fraction(1, item.rank) for item in items if item.rank is not None]
    return sum(ranks, Fraction()) if ranks else None
