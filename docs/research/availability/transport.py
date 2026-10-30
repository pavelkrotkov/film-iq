"""Provider endpoints, credential selection and one bounded request."""

import os
import re
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def endpoint(provider: str, film_id: str) -> str:
    if provider == "tmdb":
        return f"https://api.themoviedb.org/3/movie/{film_id}/watch/providers"
    return f"https://api.movieofthenight.com/v4/shows/{film_id}?country=us"


def fetch(request: Request) -> tuple[int, bytes, dict[str, str]]:
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read(), dict(response.headers)
    except HTTPError as error:
        return error.code, b"", dict(error.headers)


def quota(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower().startswith(("x-ratelimit-", "ratelimit-", "x-rate-limit-"))
        or key.lower() == "retry-after"
    }


def request_for(film: dict[str, Any], provider: str, live: bool):
    id_key, env_key, header = {
        "tmdb": ("tmdb_id", "TMDB_READ_ACCESS_TOKEN", "Authorization"),
        "motn": ("imdb_id", "MOVIE_OF_THE_NIGHT_API_KEY", "X-API-Key"),
    }[provider]
    film_id = str(film.get(id_key) or "")
    pattern = r"[1-9][0-9]*" if provider == "tmdb" else r"tt[0-9]+"
    if not re.fullmatch(pattern, film_id) or not film.get("identity_evidence"):
        return None, film_id, "unresolved_identity"
    token = os.getenv(env_key)
    if not live or not token:
        return None, film_id, "live_disabled_or_missing_credential"
    auth = f"Bearer {token}" if provider == "tmdb" else token
    return (
        Request(endpoint(provider, film_id), headers={header: auth, "Accept": "application/json"}),
        film_id,
        None,
    )
