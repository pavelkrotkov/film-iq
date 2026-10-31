"""Local accepted-source and retained-offer changes; acknowledgements contain IDs only."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from film_iq.availability.codec import timestamp
from film_iq.availability.state import retained_events


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


def source_revisions(db: sqlite3.Connection, now: datetime) -> list[dict]:
    rows = db.execute(
        "SELECT c.list_id,c.revision_id,s.name,d.url,d.accessed_at FROM current_extraction c "
        "JOIN extraction_revision r ON r.id=c.revision_id JOIN source s ON s.id=r.source_id "
        "JOIN source_document d ON d.id=r.document_id "
        "JOIN acquisition_permission p ON p.source_id=s.id "
        "WHERE p.decision='allowed' AND p.reviewed_at<=? "
        "AND (p.retain_until IS NULL OR p.retain_until>?) ORDER BY c.list_id",
        (timestamp(now), timestamp(now)),
    )
    return [
        dict(zip(("list_id", "revision_id", "source", "url", "accessed_at"), row, strict=True))
        for row in rows
    ]


def digest(db: sqlite3.Connection, previous: dict | None, now: datetime) -> tuple[dict, dict]:
    """Missing/denied sources are unknown, never removals. First use establishes a baseline."""
    sources, events = source_revisions(db, now), retained_events(db, now)
    old = previous or {"source_revisions": {}, "offer_events": []}
    revisions = {**old["source_revisions"], **{s["list_id"]: s["revision_id"] for s in sources}}
    result = {
        "baseline": previous is None,
        "assessed_at": timestamp(now),
        "source_changes": _source_changes(sources, old) if previous is not None else [],
        "offer_changes": [e for e in events if e["id"] not in old["offer_events"]]
        if previous is not None
        else [],
    }
    acknowledged = {
        "source_revisions": revisions,
        "offer_events": sorted(set(old["offer_events"]) | {e["id"] for e in events}),
    }
    return result, acknowledged


def _source_changes(sources: list[dict], previous: dict) -> list[dict]:
    return [
        {**source, "previous_revision_id": previous["source_revisions"].get(source["list_id"])}
        for source in sources
        if previous["source_revisions"].get(source["list_id"]) != source["revision_id"]
    ]


def markdown(result: dict) -> str:
    lines = ["# Film IQ — local changes", f"Assessed {result['assessed_at']}."]
    if result["baseline"]:
        lines.append(
            "First-use baseline: existing accepted sources and retained offers are not alerts."
        )
    for item in result["source_changes"]:
        action = "Updated" if item["previous_revision_id"] else "New"
        lines.append(
            f"- {action} accepted source: [{item['source']}]({item['url']}); fetched {item['accessed_at']}."
        )
    for item in result["offer_changes"]:
        change = item["change"]
        offer = change["opportunity"]
        lines.append(
            f"- {change['kind']}: TMDB {offer['film_id']}, {offer['service']} / {offer['plan'] or 'unknown plan'} ({change['source']}); observed {change['observed_at']}."
        )
    if not result["baseline"] and not (result["source_changes"] or result["offer_changes"]):
        lines.append("No new retained changes.")
    return "\n\n".join(lines) + "\n"
