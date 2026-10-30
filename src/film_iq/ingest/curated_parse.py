"""Validate a curator's factual assertions at the CSV boundary."""

from datetime import date
from urllib.parse import urlparse

from film_iq.ingest.curated_row import CuratedRow


def _positive(value: str) -> int | None:
    if not value:
        return None
    number = int(value)
    if number < 1:
        raise ValueError("numeric facts must be positive integers")
    return number


def _date(value: str) -> str | None:
    return date.fromisoformat(value).isoformat() if value else None


def parse_row(values: dict[str, str]) -> CuratedRow:
    for name in ("source_id", "source_url", "edition", "ballot_scope", "raw_title", "locator"):
        if not values[name].strip():
            raise ValueError(f"{name} is required")
    url = urlparse(values["source_url"])
    if url.scheme not in {"https", "http"} or not url.netloc:
        raise ValueError("source_url must be an absolute HTTP URL")
    position = _positive(values["position"])
    if position is None:
        raise ValueError("position is required")
    optional = {name: value or None for name, value in values.items()}
    return CuratedRow(
        values["source_id"],
        values["source_url"],
        values["edition"],
        values["ballot_scope"],
        position,
        _positive(values["rank"]),
        optional["tie"],
        _date(values["published_at"]),
        _date(values["eligibility_date"]),
        values["raw_title"],
        optional["director"],
        _positive(values["year"]),
        _positive(values["tmdb_id"]),
        optional["identity_reviewer"],
        optional["identity_evidence"],
        values["locator"],
    )
