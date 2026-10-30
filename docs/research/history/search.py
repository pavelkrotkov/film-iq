"""TMDB search transport; credentials stay out of evidence URLs."""

from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch(query: str, page: int, auth: tuple[str, str]) -> tuple[int, bytes, dict[str, str]]:
    token, api_key = auth
    params = {"query": query, "page": page, "language": "en-US", "include_adult": "false"}
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        params["api_key"] = api_key
    request = Request(
        f"https://api.themoviedb.org/3/search/movie?{urlencode(params)}", headers=headers
    )
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
