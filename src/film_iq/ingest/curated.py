"""Curated CSV preview and pending evidence, reusing acceptance/identity history."""

import json
import sqlite3
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from film_iq.ingest.adapters.page_capture import Entry, Extraction
from film_iq.ingest.curated_csv import CuratedRow, read_csv
from film_iq.ingest.curated_manifest import CuratedList
from film_iq.ingest.curated_store import persist_curated
from film_iq.ingest.persist_checks import SourcePolicy


def load_manifest(path: Path) -> CuratedList:
    data = json.loads(path.read_text())
    data["policy"] = SourcePolicy(**data["policy"])
    return CuratedList(**data)


def extraction(body: str, manifest: CuratedList) -> tuple[Extraction, tuple[CuratedRow, ...]]:
    """The checksum describes the curated record, never a publisher page capture."""
    rows = read_csv(body)
    if len(rows) != manifest.expected_count:
        raise ValueError("curated selection count differs from manifest; no truncation allowed")
    if (rows[0].source_id, rows[0].edition, rows[0].ballot_scope) != (
        manifest.policy.id,
        manifest.edition,
        manifest.ballot_scope,
    ):
        raise ValueError("CSV source/edition/ballot differs from manifest")
    entries = tuple(
        Entry(
            row.raw_title,
            json.dumps(asdict(row), ensure_ascii=False),
            row.position,
            row.rank,
            row.locator,
            row.tie,
        )
        for row in rows
    )
    captured = Extraction(
        rows[0].source_url,
        rows[0].source_url,
        manifest.document_revision,
        "curated-csv-1",
        sha256(json.dumps([body, manifest.evidence_kind], ensure_ascii=False).encode()).hexdigest(),
        manifest.eligibility,
        manifest.completeness,
        manifest.scope,
        manifest.lineage,
        manifest.rank_semantics,
        entries,
        review_reason=json.dumps(
            {
                "rights_evidence": manifest.rights_evidence,
                "permitted_use": manifest.permitted_use,
                "evidence_kind": manifest.evidence_kind,
            }
        ),
    )
    return captured, rows


def import_list(
    body: str,
    manifest: CuratedList,
    *,
    db: sqlite3.Connection | None = None,
    accessed_at: str,
    watched_tmdb_ids: frozenset[int] = frozenset(),
) -> dict:
    """Dry run by default; persistence creates pending revisions, never accepts them."""
    captured, rows = extraction(body, manifest)
    revision = None
    if db is not None:
        revision = persist_curated(db, captured, rows, manifest, accessed_at)
    candidates = [
        {
            **asdict(row),
            "identity_status": "reviewed" if row.tmdb_id else "unresolved",
            "watched": row.tmdb_id in watched_tmdb_ids if row.tmdb_id else None,
            "source_reason": f"{manifest.edition}: {manifest.scope}",
            "extraction_status": "pending_independent_acceptance",
        }
        for row in rows
    ]
    return {
        "revision_id": revision,
        "total_candidates": len(rows),
        "accepted": 0,
        "reviewed_identities": sum(row.tmdb_id is not None for row in rows),
        "unresolved": sum(row.tmdb_id is None for row in rows),
        "watched_excluded": sum(row.tmdb_id in watched_tmdb_ids for row in rows),
        "completeness": manifest.completeness,
        "lineage": manifest.lineage,
        "candidates": candidates,
    }
