"""Backend-neutral enrichment for the isolated tracker experiment.

The bundled source is synthetic; its IDs and provider names are not TMDB data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from film_iq.availability.tmdb import normalize


@dataclass(frozen=True)
class FilmMetadata:
    source_id: int
    title: str
    synopsis: str
    year: int | None
    genre: str | None


class Source(Protocol):
    def film(self, source_id: int) -> FilmMetadata: ...

    def availability(self, source_id: int) -> dict | None: ...


class Backend(Protocol):
    def ensure_film(self, film: FilmMetadata) -> str: ...

    def set_availability(self, record_id: str, value: dict) -> None: ...


def enrich(source: Source, backend: Backend, source_id: int, now: datetime) -> str:
    """Fetch first; never replace availability after a failed or partial response."""
    if type(source_id) is not int or source_id <= 0:
        raise ValueError("source ID must be a positive integer")
    film = source.film(source_id)
    if film.source_id != source_id or not film.title.strip():
        raise ValueError("source returned invalid film identity")
    observation = normalize(source_id, source.availability(source_id), now)
    record_id = backend.ensure_film(film)
    if observation.status == "complete":
        backend.set_availability(
            record_id,
            {
                "source": "synthetic fixture, not TMDB",
                "checked_at": now.isoformat(),
                "subscription": sorted(
                    {o.provider for o in observation.offers if o.kind == "subscription"}
                ),
                "rent": sorted({o.provider for o in observation.offers if o.kind == "rent"}),
                "buy": sorted({o.provider for o in observation.offers if o.kind == "buy"}),
            },
        )
    return record_id


class FixtureSource:
    """Predictable synthetic responses, never a real film or live API call."""

    def film(self, source_id: int) -> FilmMetadata:
        return FilmMetadata(
            source_id,
            f"Synthetic imported film {source_id}",
            "Synthetic source synopsis.",
            2001,
            "Drama",
        )

    def availability(self, source_id: int) -> dict | None:
        return {
            "id": source_id,
            "results": {
                "US": {
                    "link": "https://example.invalid/synthetic",
                    "flatrate": [{"provider_id": 101, "provider_name": "Fixture Stream"}],
                    "rent": [{"provider_id": 102, "provider_name": "Fixture Rental"}],
                }
            },
        }
