"""Allowlisted personal fields for reports; comments and raw provenance stay private."""

from datetime import datetime

from film_iq.discovery_personal_fields import personal_fields
from film_iq.personal_snapshot import VERSION


def personal_index(snapshot: dict | None) -> dict[int, dict]:
    if snapshot is None:
        return {}
    if snapshot.get("version") != VERSION or not isinstance(snapshot.get("films"), list):
        raise ValueError("a supported complete personal snapshot is required")
    checked = datetime.fromisoformat(snapshot["last_successful_refresh"])
    if checked.utcoffset() is None:
        raise ValueError("personal refresh time must be timezone-aware")
    films = {}
    for film in snapshot["films"]:
        identifier = film["tmdb_id"]
        _identifier(identifier, films)
        films[identifier] = personal_fields(film)
    return films


def _identifier(identifier, films):
    if type(identifier) is not int or identifier <= 0 or identifier in films:
        raise ValueError("personal TMDB identities must be positive and unique")


def fresh_snapshot(snapshot, status) -> bool:
    return (
        snapshot is not None
        and status is not None
        and status.get("stale") is False
        and status.get("last_successful_refresh") == snapshot["last_successful_refresh"]
    )
