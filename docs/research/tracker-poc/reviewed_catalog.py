"""Read already-reviewed catalog facts without copying or updating the source.

The caller must authorize access to the tracker record and enforce any
applicable approved-ID policy before returning these facts. A matching title
is only a display guard; it does not independently establish film identity.
"""

import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

from film_iq.display_catalog import read_catalog


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).lower().split())


def catalog_facts(
    path: Path | None, tmdb_id: int, tracker_title: str, now: datetime | None = None
) -> dict[str, Any] | None:
    """Return bounded facts from one fresh catalog, or None if unavailable.

    This function reads the configured file on every call and makes no network
    requests. Missing, expired, malformed, or mismatched data stays unknown.
    """
    if (
        path is None
        or type(tmdb_id) is not int
        or not 0 < tmdb_id <= 2_147_483_647
        or not isinstance(tracker_title, str)
        or not tracker_title.strip()
        or len(tracker_title) > 512
    ):
        return None
    try:
        records, context = read_catalog(path, now)
        record = records.get(tmdb_id)
        if not record:
            return None
        title, original, directors = record["title"], record["original_title"], record["directors"]
        runtime, attribution = record["runtime_minutes"], context["attribution"]
        if (
            len(title) > 512
            or len(original) > 512
            or len(directors) > 20
            or any(len(name) > 256 for name in directors)
            or (runtime is not None and runtime > 10_000)
            or len(attribution) > 1_000
        ):
            return None
        target = _normalized(tracker_title)
        if not target or target not in {_normalized(title), _normalized(original)}:
            return None
        released = record["release_date"]
        return {
            "tmdb_id": tmdb_id,
            "title": title,
            "original_title": original,
            "year": date.fromisoformat(released).year if released is not None else None,
            "directors": directors,
            "runtime_minutes": runtime,
            "source": "Reviewed display catalog",
            "observed_at": context["observed_at"],
            "expires_at": context["expires_at"],
            "attribution": attribution,
        }
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return None
