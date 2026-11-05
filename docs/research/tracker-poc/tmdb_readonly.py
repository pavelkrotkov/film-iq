"""Read one TMDB movie without retaining responses or writing tracker records.

TMDB and JustWatch attribution and retention rules must be addressed before
making this data visible or persisting it. Credentials come from environment.
"""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime

from film_iq.availability.candidate_transport import _NoRedirect
from film_iq.availability.tmdb import Observation, normalize


@dataclass(frozen=True)
class Movie:
    tmdb_id: int
    title: str
    synopsis: str | None
    year: int | None
    genres: tuple[str, ...] | None
    directors: tuple[str, ...] | None
    poster_url: str | None
    availability: Observation
    imdb_title_url: str | None = None
    original_title: str | None = None


class TMDbError(Exception):
    pass


class TMDbRateLimited(TMDbError):
    pass


def fetch(path: str, parameters: dict | None = None) -> dict:
    token, key = os.getenv("TMDB_READ_ACCESS_TOKEN"), os.getenv("TMDB_API_KEY")
    if not token and not key:
        raise TMDbError("TMDB credential is not configured")
    params = dict(parameters or {})
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        params["api_key"] = key
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"https://api.themoviedb.org/3/{path}?{query}", headers=headers
    )
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=20) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise TMDbRateLimited("TMDB returned HTTP 429") from None
        raise TMDbError(f"TMDB returned HTTP {error.code}") from None
    except (urllib.error.URLError, OSError, ValueError):
        raise TMDbError("TMDB request or response failed") from None
    if not isinstance(result, dict):
        raise TMDbError("TMDB response was not an object")
    return result


def poster_url(path, configuration: dict) -> str | None:
    images = configuration.get("images")
    if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
        return None
    if (
        not isinstance(images, dict)
        or not isinstance(images.get("poster_sizes"), list)
        or "w500" not in images["poster_sizes"]
    ):
        return None
    base = images.get("secure_base_url")
    if not isinstance(base, str) or not base.startswith("https://") or not base.endswith("/"):
        return None
    return base + "w500" + path


def release_year(value) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value).year
    except ValueError:
        return None


def read_movie(tmdb_id: int, get=fetch, now: datetime | None = None) -> Movie:
    if type(tmdb_id) is not int or tmdb_id <= 0:
        raise ValueError("TMDB ID must be a positive integer")
    details = get(f"movie/{tmdb_id}", {"append_to_response": "credits,external_ids"})
    if (
        type(details.get("id")) is not int
        or details.get("id") != tmdb_id
        or not isinstance(details.get("title"), str)
        or not details["title"].strip()
    ):
        raise TMDbError("TMDB returned invalid movie identity")
    year = release_year(details.get("release_date"))
    raw_genres = details.get("genres")
    genres = (
        tuple(item["name"] for item in raw_genres)
        if isinstance(raw_genres, list)
        and all(
            isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"].strip()
            for item in raw_genres
        )
        else None
    )
    credits = details.get("credits")
    crew = credits.get("crew") if isinstance(credits, dict) else None
    directors = (
        tuple(item["name"] for item in crew if item.get("job") == "Director")
        if isinstance(crew, list)
        and all(
            isinstance(item, dict)
            and (
                item.get("job") != "Director"
                or (isinstance(item.get("name"), str) and item["name"].strip())
            )
            for item in crew
        )
        else None
    )
    try:
        poster = poster_url(details.get("poster_path"), get("configuration"))
    except TMDbRateLimited:
        raise
    except TMDbError:
        poster = None
    try:
        available = get(f"movie/{tmdb_id}/watch/providers")
    except TMDbRateLimited:
        raise
    except TMDbError:
        available = None
    synopsis = details.get("overview")
    original_title = details.get("original_title")
    external_ids = details.get("external_ids")
    imdb_id = external_ids.get("imdb_id") if isinstance(external_ids, dict) else None
    imdb_url = (
        f"https://www.imdb.com/title/{imdb_id}/"
        if isinstance(imdb_id, str)
        and re.fullmatch(r"tt[0-9]{7,15}", imdb_id)
        and isinstance(external_ids, dict)
        and (
            "id" not in external_ids
            or (type(external_ids["id"]) is int and external_ids["id"] == tmdb_id)
        )
        else None
    )
    return Movie(
        tmdb_id,
        details["title"],
        synopsis if isinstance(synopsis, str) and synopsis else None,
        year,
        genres,
        directors,
        poster,
        normalize(tmdb_id, available, now or datetime.now(UTC)),
        imdb_url,
        original_title if isinstance(original_title, str) and original_title.strip() else None,
    )
