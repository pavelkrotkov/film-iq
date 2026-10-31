"""Current accepted work-linked components, without blending unlike evidence."""

import json
import sqlite3

KINDS = (
    "critic_selection",
    "institutional_selection",
    "registry_selection",
    "award_outcome",
    "reception_metric",
)


def current_components(db: sqlite3.Connection) -> list[dict]:
    cursor = db.execute("""
        SELECT o.entry_id,o.revision_id,m.film_id,f.tmdb_id,o.raw_title,o.listed_year,o.raw_context,
               o.rank,o.tie,l.completeness,l.rank_semantics,
               d.url,d.published_at,o.locator,l.edition,l.author,l.eligibility,
               l.lineage_kind,l.lineage,l.lineage_verification,s.id AS source_id,s.family,
               s.independence_group,s.independence_verification,
               coalesce(t.kind,'unknown') AS kind,t.payload,t.review
        FROM current_extraction c JOIN extraction_revision r ON r.id=c.revision_id
        JOIN entry_observation o ON o.revision_id=r.id AND o.extraction_decision='accepted'
        JOIN published_list l ON l.id=c.list_id JOIN source s ON s.id=l.source_id
        JOIN source_document d ON d.id=r.document_id
        JOIN current_match m ON m.entry_id=o.entry_id AND m.revision_id=o.revision_id
        JOIN film_index f ON f.id=m.film_id
        LEFT JOIN entry_recognition t ON t.entry_id=o.entry_id AND t.revision_id=o.revision_id
        WHERE r.acceptance_state='accepted' AND m.decision='accepted'
        ORDER BY o.entry_id,o.revision_id
    """)
    names = [column[0] for column in cursor.description]
    return [_decode(dict(zip(names, row, strict=True))) for row in cursor]


def _decode(row: dict) -> dict:
    payload = row.pop("payload")
    row["component"] = json.loads(payload) if payload else None
    row["classification_reviewed"] = row.pop("review") is not None
    row["published_at"] = _published(row["published_at"], row.pop("raw_context"))
    return row


def components_for(db: sqlite3.Connection | None, tmdb_id: int | None) -> dict:
    rows = (
        [] if db is None else [row for row in current_components(db) if row["tmdb_id"] == tmdb_id]
    )
    grouped = {kind: [] for kind in KINDS}
    grouped["unclassified"] = []
    for row in rows:
        grouped.get(row["kind"], grouped["unclassified"]).append(row)
    return {
        **grouped,
        "missing": [kind for kind in KINDS if not grouped[kind]],
        "interpretation": "Separate observed components; missing coverage is unknown, never zero",
    }


def _published(normalized, raw):
    if normalized is not None:
        return normalized
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data.get("published_at") if isinstance(data, dict) else None
