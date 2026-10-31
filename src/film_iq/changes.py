"""Local accepted-source and retained-offer changes; acknowledgements contain IDs only."""

import sqlite3
from datetime import datetime

from film_iq.availability.codec import timestamp
from film_iq.availability.state import retained_events


def source_revisions(db: sqlite3.Connection, now: datetime) -> list[dict]:
    rows = db.execute(
        "SELECT c.list_id,c.revision_id,s.name,d.url,d.accessed_at,a.audited_at FROM current_extraction c "
        "JOIN extraction_revision r ON r.id=c.revision_id JOIN source s ON s.id=r.source_id "
        "JOIN source_document d ON d.id=r.document_id "
        "JOIN acquisition_permission p ON p.source_id=s.id "
        "LEFT JOIN extraction_audit a ON a.revision_id=r.id "
        "WHERE r.acceptance_state='accepted' AND p.decision='allowed' AND p.reviewed_at<=? "
        "AND (p.retain_until IS NULL OR p.retain_until>?) ORDER BY c.list_id",
        (timestamp(now), timestamp(now)),
    )
    # Audits/captures may use offsets or legacy labels; do not compare their raw text.
    return [
        dict(zip(("list_id", "revision_id", "source", "url", "accessed_at"), row[:5], strict=True))
        for row in rows
        if not any(_known_future(value, now) for value in row[4:])
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


def _known_future(value: str | None, now: datetime) -> bool:
    """Legacy unparseable/undated records remain unknown, never invented instants."""
    try:
        observed = datetime.fromisoformat(value or "")
    except ValueError:
        return False
    return observed.utcoffset() is not None and observed > now
