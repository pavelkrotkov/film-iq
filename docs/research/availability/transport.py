"""Provider endpoints, credential selection and one bounded request."""

import os
import re
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
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
        # HTTPError text includes the authenticated URL; retain only status and headers.
        return error.code, b"", dict(error.headers)


def quota(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower().startswith(("x-ratelimit-", "ratelimit-", "x-rate-limit-"))
        or key.lower() == "retry-after"
    }


def authenticated_request(provider: str, film_id: str) -> Request | None:
    # Only the outbound Request may contain a key; evidence uses endpoint() separately.
    env_key, header = {
        "tmdb": ("TMDB_READ_ACCESS_TOKEN", "Authorization"),
        "motn": ("MOVIE_OF_THE_NIGHT_API_KEY", "X-API-Key"),
    }[provider]
    token = os.getenv(env_key)
    url = endpoint(provider, film_id)
    headers = {"Accept": "application/json"}
    if token:
        headers[header] = f"Bearer {token}" if provider == "tmdb" else token
    elif provider == "tmdb" and (key := os.getenv("TMDB_API_KEY")):
        url += "?" + urlencode({"api_key": key})
    else:
        return None
    return Request(url, headers=headers)


def request_for(film: dict[str, Any], provider: str, live: bool):
    id_key = {"tmdb": "tmdb_id", "motn": "imdb_id"}[provider]
    film_id = str(film.get(id_key) or "")
    pattern = r"[1-9][0-9]*" if provider == "tmdb" else r"tt[0-9]+"
    if not re.fullmatch(pattern, film_id) or not film.get("identity_evidence"):
        return None, film_id, "unresolved_identity"
    if not live:
        return None, film_id, "live_disabled_or_missing_credential"
    request = authenticated_request(provider, film_id)
    reason = None if request else "live_disabled_or_missing_credential"
    return request, film_id, reason
