"""Resolve supplied candidates without assuming missing data is negative."""

from .models import Candidate, Decision, Observation


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _id_matches(observation: Observation, candidate: Candidate) -> bool:
    pairs = ((observation.tmdb_id, candidate.tmdb_id), (observation.imdb_id, candidate.imdb_id))
    return any(a is not None and a == b for a, b in pairs)


def _ids_agree(observation: Observation, candidate: Candidate) -> bool:
    pairs = ((observation.tmdb_id, candidate.tmdb_id), (observation.imdb_id, candidate.imdb_id))
    return all(a is None or a == b for a, b in pairs)


def _title_matches(observation: Observation, candidate: Candidate) -> bool:
    return bool(
        observation.title.strip()
        and observation.director
        and candidate.director
        and observation.year is not None
        and observation.year == candidate.year
        and _normalize(observation.director) == _normalize(candidate.director)
        and _normalize(observation.title) in map(_normalize, candidate.titles)
    )


def _select(
    observation: Observation, candidates: tuple[Candidate, ...]
) -> tuple[tuple[Candidate, ...], bool, str, str]:
    if observation.tmdb_id is not None or observation.imdb_id is not None:
        matches = tuple(c for c in candidates if _id_matches(observation, c))
        return (
            matches,
            len(matches) == 1 and _ids_agree(observation, matches[0]),
            "external_id",
            "External identifiers must agree uniquely",
        )
    matches = tuple(c for c in candidates if _title_matches(observation, c))
    return (
        matches,
        len(matches) == 1,
        "title_director_year",
        "Exact normalized title or alias, director and year",
    )


def resolve(observation: Observation, candidates: tuple[Candidate, ...]) -> Decision:
    """Prefer consistent external IDs; otherwise require title, director and year."""
    matches, accepted, method, evidence = _select(observation, candidates)
    return Decision(
        observation,
        tuple(c.tmdb_id for c in candidates),
        matches[0].tmdb_id if accepted else None,
        method,
        evidence,
        candidate_evidence=candidates,
    )
