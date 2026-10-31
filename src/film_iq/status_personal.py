"""Reuse complete personal schema and generation checks without printing film data."""

import json
from datetime import datetime
from pathlib import Path

from film_iq.discovery_personal import fresh_snapshot, personal_index
from film_iq.status_run import checked_time


def personal_status(path: Path, now: datetime) -> dict:
    snapshot = json.loads(path.read_text())
    personal_index(snapshot)
    last = checked_time(snapshot["last_successful_refresh"], now)
    marker = json.loads(path.with_suffix(path.suffix + ".status").read_text())
    if type(marker["stale"]) is not bool:
        raise ValueError("invalid snapshot status")
    return {
        "state": "current" if fresh_snapshot(snapshot, marker) else "stale",
        "last_successful_refresh": last,
    }
