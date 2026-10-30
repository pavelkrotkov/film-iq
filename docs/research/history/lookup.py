"""Bounded paginated search with explicit unknown and review states."""

import hashlib
import json
import os
from datetime import UTC, datetime
from http.client import HTTPException
from typing import Any
from urllib.error import URLError

from .search import fetch, quota
from .validation import candidates, complete


def read_page(query: str, page: int, token: str, get, attempts: list) -> dict:
    attempt: dict[str, Any] = {
        "page": page,
        "observed_at": datetime.now(UTC).isoformat(),
        "phase": "transport",
    }
    attempts.append(attempt)
    status, body, headers = get(query, page, token)
    attempt.update(http_status=status, quota=quota(headers), phase="http_status")
    if status != 200:
        raise ValueError("unsuccessful search")
    attempt["response_sha256"] = hashlib.sha256(body).hexdigest()
    attempt["phase"] = "json_decode"
    data = json.loads(body)
    attempt["phase"] = "schema"
    attempt["candidates"] = candidates(data, page)
    attempt.update(
        total_pages=data["total_pages"], total_results=data["total_results"], phase="complete"
    )
    return data


def pages(query: str, token: str, limit: int, get, attempts: list) -> list[dict]:
    first = read_page(query, 1, token, get, attempts)
    total_pages, total_results = first["total_pages"], first["total_results"]
    # A request budget must never silently truncate the candidate set.
    if total_pages > limit:
        attempts[-1]["phase"] = "page_budget"
        raise ValueError("page limit: incomplete candidate set")
    for page in range(2, total_pages + 1):
        data = read_page(query, page, token, get, attempts)
        if (data["total_pages"], data["total_results"]) != (total_pages, total_results):
            attempts[-1]["phase"] = "pagination_consistency"
            raise ValueError("pagination changed")
    rows = [row for attempt in attempts for row in attempt["candidates"]]
    attempts[-1]["phase"] = "result_set"
    complete(rows, total_results)
    attempts[-1]["phase"] = "complete"
    return rows


def lookup(film: dict, live: bool = False, max_pages: int = 5, get=fetch) -> dict:
    result: dict[str, Any] = {
        "key": film["key"],
        "query": film["query"],
        "endpoint": "https://api.themoviedb.org/3/search/movie",
        "query_parameters": {"language": "en-US", "include_adult": False},
        "state": "unknown",
        "identity": "unreviewed",
        "confirmed_absent": False,
        "reason": "live_disabled_or_missing_credential",
        "attempts": [],
        "monetary_cost": None,
    }
    token = os.getenv("TMDB_READ_ACCESS_TOKEN")
    if not live or not token:
        return result | {"requests": 0}
    try:
        rows = pages(film["query"], token, max_pages, get, result["attempts"])
        result.update(state="complete_search", reason=None, candidates=rows)
    # Retain successful earlier pages as partial evidence, never as a complete set.
    except (HTTPException, URLError, OSError, ValueError, KeyError, TypeError) as error:
        result.update(
            reason="failed_or_incomplete_search",
            failure={"phase": result["attempts"][-1]["phase"], "type": type(error).__name__},
        )
    return result | {"requests": len(result["attempts"])}
