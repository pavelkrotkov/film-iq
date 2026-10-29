"""Immutable identity observations and decision records."""

from dataclasses import dataclass


class _NormalizeMissing:
    def __post_init__(self) -> None:
        # Blank optional identity fields represent missing information. Preserve
        # nonblank values as supplied so the decision retains source evidence.
        for field in ("director", "imdb_id"):
            value = getattr(self, field)
            if value is not None and not value.strip():
                object.__setattr__(self, field, None)


@dataclass(frozen=True)
class Observation(_NormalizeMissing):
    title: str
    director: str | None = None
    year: int | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = None


@dataclass(frozen=True)
class Candidate(_NormalizeMissing):
    tmdb_id: int
    titles: tuple[str, ...]
    director: str | None = None
    year: int | None = None
    imdb_id: str | None = None


@dataclass(frozen=True)
class Decision:
    observation: Observation
    candidates: tuple[int, ...]
    match: int | None
    method: str
    evidence: str
    reviewer: str | None = None
    version: str = "1"
    candidate_evidence: tuple[Candidate, ...] = ()
