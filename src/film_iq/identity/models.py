"""Immutable identity observations and decision records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Observation:
    title: str
    director: str | None = None
    year: int | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = None


@dataclass(frozen=True)
class Candidate:
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
