"""Normalize a TMDB movie watch-providers response, attributed to JustWatch.

Input is a successful decoded response, or None on fetch/decoding failure. TMDB
and JustWatch terms, attribution and retention must be checked before storage or
presentation. This module neither fetches nor retains provider data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


@dataclass(frozen=True)
class Offer:
    film_id: int
    provider_id: int
    provider: str
    kind: Literal["subscription", "rent", "buy", "free", "ads"]
    url: str
    checked_at: datetime
    entitlement: str = "unconfirmed"
    source: str = "TMDB / JustWatch"


@dataclass(frozen=True)
class Observation:
    offers: tuple[Offer, ...]
    status: Literal["complete", "partial", "unknown"]
    checked_at: datetime


CATEGORIES = {
    "flatrate": "subscription",
    "rent": "rent",
    "buy": "buy",
    "free": "free",
    "ads": "ads",
}


def _us(film_id: int, payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or payload.get("id") != film_id:
        return None
    results = payload.get("results")
    if not isinstance(results, dict) or not isinstance(results.get("US"), dict):
        return None
    us = results["US"]
    return us if isinstance(us.get("link"), str) and us["link"] else None


def _valid(entry: Any) -> bool:
    return (
        isinstance(entry, dict)
        and type(entry.get("provider_id")) is int
        and isinstance(entry.get("provider_name"), str)
        and bool(entry["provider_name"])
    )


def _category(
    film_id: int, entries: Any, kind: Any, link: str, checked_at: datetime
) -> tuple[list[Offer], bool]:
    if not isinstance(entries, list):
        return [], True
    offers = [
        Offer(film_id, e["provider_id"], e["provider_name"], kind, link, checked_at)
        for e in entries
        if _valid(e)
    ]
    return offers, len(offers) != len(entries)


def normalize(film_id: int, payload: Any, checked_at: datetime) -> Observation:
    """Missing US, unsupported categories and invalid responses never imply removal."""
    if checked_at.utcoffset() is None:
        raise ValueError("checked_at must be timezone-aware")
    us = _us(film_id, payload)
    if us is None:
        return Observation((), "unknown", checked_at)
    offers: list[Offer] = []
    partial = bool(us.keys() - (CATEGORIES.keys() | {"link"}))
    for category, kind in CATEGORIES.items():
        found, invalid = _category(film_id, us.get(category, []), kind, us["link"], checked_at)
        offers.extend(found)
        partial |= invalid
    return Observation(
        tuple(dict.fromkeys(offers)), "partial" if partial else "complete", checked_at
    )
