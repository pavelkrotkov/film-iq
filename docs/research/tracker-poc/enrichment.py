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


class AvailabilityRefreshError(RuntimeError):
    """Film persistence succeeded but the separate provider request failed.

    Callers can inspect ``source_error`` for rate-limit or authorization
    handling. Its text is not included in the displayed error, as an upstream
    exception may contain a credential-bearing URL.
    """

    def __init__(self, record_id: str, source_error: Exception) -> None:
        super().__init__("Film saved, but availability refresh failed")
        self.record_id = record_id
        self.source_error = source_error


def enrich(source: Source, backend: Backend, source_id: int, now: datetime) -> str:
    """Save film metadata even when availability fails, without replacing offers."""
    if type(source_id) is not int or source_id <= 0:
        raise ValueError("source ID must be a positive integer")
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("checked_at must be timezone-aware")
    film = source.film(source_id)
    if film.source_id != source_id or not film.title.strip():
        raise ValueError("source returned invalid film identity")
    source_failure = None
    try:
        payload = source.availability(source_id)
    except Exception as error:
        source_failure = error
        payload = None
    observation = normalize(source_id, payload, now) if source_failure is None else None
    record_id = backend.ensure_film(film)
    if not isinstance(record_id, str) or not record_id.strip():
        raise ValueError("Film persistence returned no record ID")
    if source_failure is not None:
        raise AvailabilityRefreshError(record_id, source_failure) from None
    if observation is not None and observation.status == "complete":
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
