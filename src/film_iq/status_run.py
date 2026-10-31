"""Validate operation timestamps without inventing a refresh-age policy."""

import json
from datetime import UTC, datetime
from pathlib import Path


def checked_time(value, now: datetime) -> str | None:
    if value is None:
        return None
    stamp = datetime.fromisoformat(value)
    if stamp.utcoffset() is None or stamp > now:
        raise ValueError("invalid status timestamp")
    return stamp.astimezone(UTC).isoformat()


def run_status(path: Path, now: datetime) -> dict:
    data = json.loads(path.read_text())
    if data["version"] != "private-run-v1" or type(data["stale"]) is not bool:
        raise ValueError("unsupported run status")
    last = checked_time(data["last_successful_run"], now)
    attempted = checked_time(data["attempted_at"], now)
    if attempted is None or (not data["stale"] and (last is None or last < attempted)):
        raise ValueError("incomplete run status")
    return {"state": "stale" if data["stale"] else "current", "last_successful_run": last}
