"""Validate the private IDs-only consumer checkpoint."""

import json
from pathlib import Path


def checkpoint(path: Path) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    if set(data) != {"source_revisions", "offer_events"}:
        raise ValueError("invalid changes checkpoint")
    if not isinstance(data["source_revisions"], dict) or not isinstance(data["offer_events"], list):
        raise ValueError("invalid changes checkpoint IDs")
    values = [*data["source_revisions"], *data["source_revisions"].values(), *data["offer_events"]]
    if not all(isinstance(value, str) and value for value in values):
        raise ValueError("checkpoint IDs must be nonempty strings")
    return data
