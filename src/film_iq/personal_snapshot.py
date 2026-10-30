"""Disposable private personal state; never infer artistic merit from criticism."""

from datetime import UTC, datetime
from typing import Any

from film_iq.personal_identity import api_movies, index
from film_iq.personal_merit import merit

VERSION = "movary-personal-v1"


def _enjoyment(rows: list[dict[str, str]]) -> int | None:
    values = {int(row["userRating"]) for row in rows}
    if len(values) > 1:
        raise ValueError("Conflicting enjoyment ratings in complete export")
    return next(iter(values), None)


def _film(tmdb: int, api: dict, ratings: list[dict], history: list[dict]) -> dict:
    artistic, state = merit(history)
    source = (ratings or history or [api])[0]
    return {
        "tmdb_id": tmdb,
        "movary_id": api.get("movary_id"),
        "title": source.get("title"),
        "watched": bool(history) or api.get("played", False) or api.get("history", False),
        "watchlist": api.get("watchlist", False),
        "watched_dates": sorted({row["watchedAt"] or None for row in history}, key=str),
        "personal_enjoyment": _enjoyment(ratings),
        "personal_artistic_merit": artistic,
        "merit_status": state,
        "rating_provenance": {
            "enjoyment": "user:export:ratings",
            "merit": "user:export:history/comment",
        },
    }


def build_snapshot(
    collections: dict[str, list[dict]], ratings: list[dict], history: list[dict]
) -> dict[str, Any]:
    api, rated, watched = api_movies(collections), index(ratings), index(history)
    ids = sorted(api.keys() | rated.keys() | watched.keys())
    return {
        "version": VERSION,
        "last_successful_refresh": datetime.now(UTC).isoformat(),
        "films": [
            _film(tmdb, api.get(tmdb, {}), rated.get(tmdb, []), watched.get(tmdb, []))
            for tmdb in ids
        ],
        "unresolved": {
            "ratings": [r for r in ratings if not r["tmdbId"]],
            "history": [r for r in history if not r["tmdbId"]],
        },
        "provenance": {"api": collections, "ratings_csv": ratings, "history_csv": history},
    }
