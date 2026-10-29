"""Read verified, current A1 observations as scoring inputs."""

import sqlite3
from datetime import date

from film_iq.scoring import Evidence


def load_evidence(db: sqlite3.Connection) -> list[Evidence]:
    """Read only explicitly accepted matches and verified original evidence."""
    rows = db.execute("""
        SELECT m.film_id, l.id, d.url, d.published_at, s.independence_group,
               l.eligibility, o.rank, o.entry_id, o.revision_id, m.decision_id,
               s.id, d.id, o.locator
        FROM current_extraction AS c
        JOIN extraction_revision AS r ON r.id = c.revision_id AND r.list_id = c.list_id
        JOIN published_list AS l ON l.id = c.list_id
        JOIN source AS s ON s.id = l.source_id
        JOIN source_document AS d ON d.id = r.document_id
        JOIN entry_observation AS o ON o.revision_id = r.id AND o.list_id = l.id
        JOIN current_match AS m ON m.entry_id = o.entry_id AND m.revision_id = o.revision_id
        WHERE r.acceptance_state = 'accepted' AND o.extraction_decision = 'accepted'
          AND m.decision = 'accepted' AND s.independence_verification = 'verified'
          AND length(trim(s.independence_group)) > 0
          AND l.lineage_verification = 'verified' AND l.lineage_kind = 'original'
        ORDER BY o.entry_id, o.revision_id
    """).fetchall()
    return [
        Evidence(
            film_id=str(film),
            list_id=list_id,
            url=url,
            published=date.fromisoformat(published[:10]) if published else None,
            independence_group=group,
            eligibility=eligibility,
            rank=rank,
            entry_id=entry,
            revision_id=revision,
            match_decision_id=match,
            source_id=source,
            document_id=document,
            locator=locator,
        )
        for (
            film,
            list_id,
            url,
            published,
            group,
            eligibility,
            rank,
            entry,
            revision,
            match,
            source,
            document,
            locator,
        ) in rows
    ]
