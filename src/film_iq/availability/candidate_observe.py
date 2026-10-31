"""Convert one bounded response to a validated observation, never an error-as-absence."""

import json
from collections.abc import Callable
from datetime import datetime
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import Request

from film_iq.availability import candidate_native, candidate_tmdb
from film_iq.availability.candidate_models import ReviewedWork
from film_iq.availability.candidate_transport import Response
from film_iq.availability.fetch import Fetch

MAPPERS = {"tmdb": candidate_tmdb.normalize, "motn": candidate_native.normalize}


def observe(
    provider: str,
    work: ReviewedWork,
    request: Request,
    checked_at: datetime,
    get: Callable[[Request], Response],
) -> tuple[Fetch, str | None, dict[str, int]]:
    unknown = Fetch(provider, work.tmdb_id, "US", checked_at, "unknown", work_reviewed=True)
    quota = {}
    try:
        status, body, headers = get(request)
        quota = _quota(headers)
        if type(status) is not int or not 100 <= status <= 599:
            return unknown, "invalid_response", quota
        if status != 200:
            return unknown, f"http_{status}", quota
        payload = json.loads(body)
        if not isinstance(payload, dict):
            return unknown, "invalid_response", quota
        result = MAPPERS[provider](work, payload, checked_at)
        return result, None if result.status == "complete" else "incomplete_response", quota
    except (
        HTTPException,
        URLError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        OverflowError,
    ):
        return unknown, "request_or_validation_error", quota


def _quota(headers: dict[str, str]) -> dict[str, int]:
    names = {"x-ratelimit-remaining", "x-ratelimit-requests-remaining", "ratelimit-remaining"}
    return {
        key.lower(): int(value)
        for key, value in headers.items()
        if key.lower() in names and value.isdecimal()
    }
