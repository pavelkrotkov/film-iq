"""Read Movary 0.82.1 API data and publish complete ratings exports.

The caller supplies an authorized account and runs the export in its Movary
installation. Snapshots contain private data and must be stored accordingly.
"""

import csv
import json
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


class MovaryClient:
    def __init__(self, base_url: str, username: str, token: str):
        self.url = f"{base_url.rstrip('/')}/api/v1/users/{quote(username, safe='')}"
        self.token = token

    def read(self, collection: str) -> list[dict]:
        """Fetch every page, raising instead of returning a partial result."""
        if collection not in ("played", "history", "watchlist"):
            raise ValueError("Unsupported Movary collection")
        results: list[dict] = []
        page = 1
        maximum = None
        while True:
            request = Request(
                f"{self.url}/{collection}/movies?page={page}&limit=100",
                headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
            )
            with urlopen(request, timeout=30) as response:
                data = json.load(response)
            entries, last = _page(data, collection, page, maximum)
            results.extend(entries)
            if not entries and (page > 1 or page < last):
                raise ValueError("Empty advertised Movary page")
            if page >= last:
                return results
            maximum = last
            page += 1


def _page(data: dict, collection: str, page: int, maximum: int | None) -> tuple[list[dict], int]:
    entries = data.get(collection)
    current, last = data.get("currentPage"), data.get("maxPage")
    if (
        not isinstance(entries, list)
        or not all(isinstance(x, dict) for x in entries)
        or type(current) is not int
        or type(last) is not int
        or current != page
    ):
        raise ValueError("Invalid Movary page")
    _check_page_bounds(entries, page, last, maximum)
    return entries, last


def _check_page_bounds(entries: list, page: int, last: int, maximum: int | None) -> None:
    if last < 0 or (maximum is not None and last != maximum):
        raise ValueError("Inconsistent Movary pagination")
    if last == 0:
        if page != 1 or entries:
            raise ValueError("Inconsistent Movary pagination")
    elif page > last:
        raise ValueError("Inconsistent Movary pagination")


_HEADER = ["title", "year", "tmdbId", "imdbId", "userRating"]


def read_ratings(path: Path) -> list[dict[str, str]]:
    """Read a completed Movary ratings export, preserving its source identifiers."""
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, strict=True)
        if reader.fieldnames != _HEADER:
            raise ValueError("Invalid Movary ratings CSV header")
        rows = list(reader)
    for row in rows:
        _validate_rating(row)
    return rows


def _validate_rating(row: dict[str, str]) -> None:
    if (
        None in row
        or any(value is None for value in row.values())
        or not row["title"]
        or row["userRating"] not in {str(n) for n in range(1, 11)}
    ):
        raise ValueError("Invalid Movary ratings CSV row")
    _validate_tmdb(row["tmdbId"])


def _validate_tmdb(tmdb: str) -> None:
    if tmdb and (not tmdb.isdigit() or int(tmdb) < 1):
        raise ValueError("Invalid TMDB ID")


def export_ratings(command: list[str], snapshot: Path) -> list[dict[str, str]]:
    """Run user:export:ratings with a temporary output and atomically replace snapshot.

    command includes the executable, user:export:ratings and user ID; the
    export filename is appended. Both paths must be visible to the command.
    A failed command or invalid CSV leaves the previous snapshot untouched.
    """
    with tempfile.TemporaryDirectory(dir=snapshot.parent, prefix=".movary-") as directory:
        output = Path(directory) / "ratings.csv"
        subprocess.run([*command, str(output.resolve())], check=True, timeout=300)
        rows = read_ratings(output)
        os.replace(output, snapshot)
    return rows
