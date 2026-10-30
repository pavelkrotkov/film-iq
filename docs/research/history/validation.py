"""Validate entire result sets before claiming that a search completed."""

from typing import Any

FIELDS = ("id", "title", "original_title", "release_date", "original_language")


def pagination(data: dict, page: int) -> None:
    counts = (data["page"], data["total_pages"], data["total_results"])
    if any(type(value) is not int or value < 0 for value in counts):
        raise ValueError("invalid pagination counts")
    # TMDB represents an empty search as page 1 with zero total pages/results.
    if counts[0] != page or (counts[1] < page and counts[1:] != (0, 0)):
        raise ValueError("incorrect page")


def candidate(row: dict) -> dict[str, Any]:
    result = {key: row[key] for key in FIELDS}
    if type(result["id"]) is not int or result["id"] <= 0:
        raise ValueError("invalid candidate ID")
    if any(not isinstance(result[key], str) for key in FIELDS[1:]):
        raise ValueError("invalid candidate metadata")
    return result


def candidates(data: dict, page: int) -> list[dict]:
    pagination(data, page)
    if not isinstance(data["results"], list):
        raise ValueError("missing result list")
    return [candidate(row) for row in data["results"]]


def complete(rows: list[dict], total: int) -> None:
    # Repeated candidates can conceal missing rows even when counts agree.
    if len(rows) != total or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("incomplete or duplicate result set")
