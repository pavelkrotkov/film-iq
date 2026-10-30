"""Validate Movary 0.82.1 history CSV and explicit personal-merit assertions."""

import csv
from datetime import date
from pathlib import Path

_HEADER = ["title", "year", "tmdbId", "imdbId", "watchedAt", "comment", "location"]


def read_history(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, strict=True)
        if reader.fieldnames != _HEADER:
            raise ValueError("Invalid Movary history CSV header")
        rows = list(reader)
    for row in rows:
        _validate(row)
    return rows


def _validate(row: dict[str, str]) -> None:
    if None in row or any(value is None for value in row.values()) or not row["title"]:
        raise ValueError("Invalid Movary history CSV row")
    tmdb = row["tmdbId"]
    _validate_tmdb(tmdb)
    if row["watchedAt"]:
        date.fromisoformat(row["watchedAt"])


def _validate_tmdb(tmdb: str) -> None:
    if tmdb and (not tmdb.isdigit() or int(tmdb) < 1):
        raise ValueError("Invalid history TMDB ID")
