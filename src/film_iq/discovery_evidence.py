"""Read current accepted curated records; preview claims never grant acceptance."""

import json
import sqlite3
from dataclasses import asdict

from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence


def accepted_row(db: sqlite3.Connection | None, revision: str | None, position: int):
    if db is None or revision is None:
        return None
    cursor = db.execute(
        """SELECT o.raw_context, f.tmdb_id,
        l.completeness AS accepted_completeness, l.lineage_kind AS accepted_lineage_kind,
        l.lineage AS accepted_lineage, l.eligibility AS accepted_eligibility,
        o.raw_title, o.listed_year AS year, o.director, o.position, o.rank, o.tie, o.locator,
        l.edition, l.author AS ballot_scope, l.source_id,
        d.url AS source_url, d.published_at
        FROM current_extraction c
        JOIN extraction_revision r ON r.id=c.revision_id AND r.acceptance_state='accepted'
        JOIN published_list l ON l.id=c.list_id
        JOIN source_document d ON d.id=r.document_id
        JOIN entry_observation o ON o.revision_id=r.id AND o.extraction_decision='accepted'
        LEFT JOIN current_match m ON m.entry_id=o.entry_id AND m.revision_id=o.revision_id
        LEFT JOIN film_index f ON f.id=m.film_id
        WHERE r.id=? AND o.position=?""",
        (revision, position),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    facts = json.loads(row[0])
    names = [column[0] for column in cursor.description]
    facts.update(zip(names[2:], row[2:], strict=True))
    return facts, row[1]


def recognition(db: sqlite3.Connection | None) -> dict[int, dict]:
    if db is None:
        return {}
    crosswalk = dict(db.execute("SELECT id,tmdb_id FROM film_index WHERE tmdb_id IS NOT NULL"))
    return {
        crosswalk[int(result.film_id)]: asdict(result)
        for result in score(load_evidence(db))
        if int(result.film_id) in crosswalk
    }


def validate_cohort(cohort: dict) -> list[dict]:
    rows = cohort["candidates"]
    if not isinstance(rows, list) or len(rows) != cohort["total_candidates"]:
        raise ValueError("cohort count must match all supplied candidates")
    positions = [row["position"] for row in rows]
    if len(positions) != len(set(positions)):
        raise ValueError("cohort positions must be unique")
    return rows
