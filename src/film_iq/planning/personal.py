"""Join the complete private personal snapshot without exposing raw provenance."""

from dataclasses import replace

from film_iq.discovery_personal import fresh_snapshot, personal_index
from film_iq.planning.models import Film


def apply_personal(films: list[Film], snapshot: dict | None, status: dict | None) -> list[Film]:
    """A supplied failed/mismatched refresh cannot yield a watch plan."""
    if snapshot is None:
        return films
    people = personal_index(snapshot)
    if not fresh_snapshot(snapshot, status):
        raise ValueError("refresh the personal snapshot successfully before planning")
    return [_replace(film, people.get(film.id, {})) for film in films]


def _replace(film: Film, personal: dict) -> Film:
    return replace(
        film,
        watched=personal.get("watched", False),
        personal_enjoyment=personal.get("personal_enjoyment"),
        personal_artistic_merit=personal.get("personal_artistic_merit"),
    )
