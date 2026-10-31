"""Read a finite reviewed display snapshot; it never establishes film identity."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from film_iq.display_catalog_records import catalog_records, required_text


def read_catalog(path: Path | None, now: datetime | None = None) -> tuple[dict[int, dict], dict]:
    if path is None:
        return {}, {"status": "not_supplied"}
    payload = json.loads(path.read_text())
    context = _context(payload, now or datetime.now(UTC))
    records = catalog_records(payload["records"])
    return (records if context["status"] == "fresh" else {}), context


def _context(payload: dict, now: datetime) -> dict:
    if payload["version"] != "reviewed-display-v1":
        raise ValueError("unsupported reviewed display version")
    observed = datetime.fromisoformat(payload["observed_at"])
    expires = datetime.fromisoformat(payload["expires_at"])
    if any(value.utcoffset() is None for value in (observed, expires, now)):
        raise ValueError("display metadata times must be timezone-aware")
    if not timedelta() < expires - observed <= timedelta(days=180):
        raise ValueError("display metadata expiry must be within180days of observation")
    attribution = required_text(payload["attribution"])
    return {
        "status": _status(observed, expires, now),
        "observed_at": observed.isoformat(),
        "expires_at": expires.isoformat(),
        "attribution": attribution,
    }


def _status(observed: datetime, expires: datetime, now: datetime) -> str:
    if now < observed:
        return "not_yet_valid"
    return "expired" if now >= expires else "fresh"
