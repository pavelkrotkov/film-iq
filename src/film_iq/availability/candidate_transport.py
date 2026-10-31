"""One authenticated outbound request; no redirects/retries or persisted secret URLs."""

import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from film_iq.availability.candidate_models import ReviewedWork


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(provider: str, work: ReviewedWork) -> Request:
    endpoints = {
        "tmdb": f"https://api.themoviedb.org/3/movie/{work.tmdb_id}/watch/providers",
        "motn": f"https://api.movieofthenight.com/v4/shows/{work.imdb_id}?country=us",
    }
    credentials = {
        "tmdb": ("TMDB_READ_ACCESS_TOKEN", "Authorization"),
        "motn": ("MOVIE_OF_THE_NIGHT_API_KEY", "X-API-Key"),
    }
    env, header = credentials[provider]
    token = os.getenv(env)
    if not token:
        if provider == "tmdb" and (key := os.getenv("TMDB_API_KEY")):
            return Request(
                endpoints[provider] + "?" + urlencode({"api_key": key}),
                headers={"Accept": "application/json"},
            )
        raise ValueError("selected provider credential is not configured")
    value = f"Bearer {token}" if provider == "tmdb" else token
    return Request(endpoints[provider], headers={"Accept": "application/json", header: value})


Response = tuple[int, bytes, dict[str, str]]


def fetch(request: Request) -> Response:
    try:
        with build_opener(_NoRedirect).open(request, timeout=30) as response:
            return response.status, response.read(), dict(response.headers)
    except HTTPError as error:
        return error.code, b"", dict(error.headers or {})
