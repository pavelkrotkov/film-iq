"""One US observation; failed or partial responses remain unknown."""

import hashlib
import json
from datetime import UTC, datetime
from http.client import HTTPException
from typing import Any
from urllib.error import URLError

from .motn_rows import motn_rows
from .provider_rows import tmdb_rows
from .transport import endpoint, fetch, quota, request_for

PROVIDERS = {"tmdb": tmdb_rows, "motn": motn_rows}


def observe(film: dict[str, Any], provider: str, live: bool, get=fetch) -> dict[str, Any]:
    normalize = PROVIDERS[provider]
    result: dict[str, Any] = {
        "key": film["key"],
        "stratum": film["stratum"],
        "provider": provider,
        "observed_at": datetime.now(UTC).isoformat(),
        "country": "US",
        "state": "unknown",
        "reason": "not_requested",
        "requests": 0,
    }
    request, film_id, reason = request_for(film, provider, live)
    if request is None:
        return result | {"reason": reason}
    result.update(endpoint=endpoint(provider, film_id), requests=1)
    phase = "transport"
    try:
        status, body, headers = get(request)
        phase = "http_status"
        result.update(http_status=status, quota=quota(headers))
        if status != 200:
            return result | {"reason": "http_error"}
        result["response_sha256"] = hashlib.sha256(body).hexdigest()
        phase = "json_decode"
        data = json.loads(body)
        phase = "schema"
        rows = normalize(data, film_id)
        return result | {
            "state": "complete_response",
            "reason": None,
            "offers": rows,
        }
    except (
        HTTPException,
        URLError,
        TimeoutError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ) as error:
        return result | {
            "reason": "transport_or_schema_error",
            "failure": {"phase": phase, "type": type(error).__name__},
        }
