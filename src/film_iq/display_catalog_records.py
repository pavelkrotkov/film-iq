"""Validate only the factual fields needed for reviewed film-card display."""

from datetime import date


def required_text(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("reviewed display text must be nonblank")
    return value


def _texts(value) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("reviewed display lists must be nonempty")
    return [required_text(item) for item in value]


def _record(item: dict) -> dict:
    identifier, minutes = item["tmdb_id"], item["runtime_minutes"]
    values = [identifier] if minutes is None else [identifier, minutes]
    if any(type(value) is not int or value <= 0 for value in values):
        raise ValueError("display IDs/runtimes must be positive integers; runtime may be unknown")
    released = (
        date.fromisoformat(item["release_date"]).isoformat()
        if item["release_date"] is not None
        else None
    )
    return {
        "tmdb_id": identifier,
        "title": required_text(item["title"]),
        "original_title": required_text(item["original_title"]),
        "directors": _texts(item["directors"]),
        "release_date": released,
        "runtime_minutes": minutes,
        "reviewer": required_text(item["reviewer"]),
        "evidence": _texts(item["evidence"]),
    }


def catalog_records(items: list) -> dict[int, dict]:
    if not isinstance(items, list):
        raise ValueError("reviewed display records must be an array")
    records = [_record(item) for item in items]
    index = {record["tmdb_id"]: record for record in records}
    if len(index) != len(records):
        raise ValueError("reviewed display TMDB IDs must be unique")
    return index
