"""Pure, provisional public-evidence baselines; no personal preference model.

Each input is one accepted observation for an identified film. Independence groups
must already account for shared critics and source families; derivative observations
are retained for explanation but never contribute. Rank is a true published rank,
not display order. A missing rank is unknown, not a zero score.
"""

from fractions import Fraction

from .models import Evidence, Score
from .policy import DEFAULT_POLICY, ScoringPolicy

VERSION = "independent-priority-rank-v2"
LEGACY_VERSION = "independent-reciprocal-rank-v1"


def score(evidence: list[Evidence], *, policy: ScoringPolicy = DEFAULT_POLICY) -> tuple[Score, ...]:
    """Rank films by independent count, then reciprocal-rank sum, then ID.

    Predeclared source/window priority selects repeated ballots without looking
    at rank. Unknown contributor identities remain unknown; independent_count
    is reviewed evidence-group support, not a count of independent people.
    """
    return _score(evidence, policy, VERSION)


def _score(evidence: list[Evidence], policy: ScoringPolicy, version: str) -> tuple[Score, ...]:
    films: dict[str, set[Evidence]] = {}
    for item in evidence:
        films.setdefault(item.film_id, set()).add(item)
    results = [_score_film(film_id, items, policy, version) for film_id, items in films.items()]
    return tuple(
        sorted(
            results, key=lambda s: (-s.independent_count, -(s.rank_score or Fraction()), s.film_id)
        )
    )


def _score_film(film_id: str, items: set[Evidence], policy: ScoringPolicy, version: str) -> Score:
    chosen = policy.choose(items, legacy=version == LEGACY_VERSION)
    contributing = tuple(sorted(chosen.values(), key=_evidence_key))
    return Score(
        film_id=film_id,
        version=version,
        independent_count=len(contributing),
        rank_score=_rank_score(contributing),
        contributing=contributing,
        excluded=tuple(sorted(items - set(contributing), key=_evidence_key)),
        unranked_count=sum(item.rank is None for item in contributing),
        partial_count=sum(item.completeness == "partial" for item in contributing),
        known_person_count=len({item.person_id for item in contributing if item.person_id}),
        unknown_contributor_count=sum(item.person_id is None for item in contributing),
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
        _optional_key(item.entry_id),
        _optional_key(item.revision_id),
        _optional_key(item.match_decision_id),
        _optional_key(item.source_id),
        _optional_key(item.document_id),
        _optional_key(item.locator),
        _optional_key(item.lineage_kind),
        _optional_key(item.lineage),
        _optional_key(item.author),
        _optional_key(item.completeness),
        _optional_key(item.rank_semantics),
        _optional_key(item.person_id),
        _optional_key(item.source_family),
    )


def _optional_key(value: str | None) -> tuple[bool, str]:
    return value is not None, value or ""


def _rank_score(items: tuple[Evidence, ...]) -> Fraction | None:
    ranks = [Fraction(1, item.rank) for item in items if item.rank is not None]
    return sum(ranks, Fraction()) if ranks else None
