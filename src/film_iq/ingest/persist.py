"""Persist provisional adapter output without promoting it to accepted evidence."""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict
from hashlib import sha256

from film_iq.ingest.adapters import film_registry, nbr_2023
from film_iq.ingest.persist_checks import (
    SourcePolicy,
    _check_list,
    _check_output,
    _ensure_source,
    _key,
)
from film_iq.ingest.persist_entries import _observations, _store_entries


@contextmanager
def _savepoint(db: sqlite3.Connection) -> Generator[None]:
    db.execute("SAVEPOINT persist_extraction")
    try:
        yield
    except BaseException:
        db.execute("ROLLBACK TO persist_extraction")
        db.execute("RELEASE persist_extraction")
        raise
    db.execute("RELEASE persist_extraction")


def persist(
    db: sqlite3.Connection,
    extraction: nbr_2023.Extraction | film_registry.Extraction,
    policy: SourcePolicy,
    edition: str,
    accessed_at: str,
) -> str:
    """Store one complete frozen extraction as pending; unchanged input is idempotent."""
    if not all(value.strip() for value in (*asdict(policy).values(), edition, accessed_at)):
        raise ValueError("source rights, edition and access time are required")
    if not db.execute("PRAGMA foreign_keys").fetchone()[0]:
        raise ValueError("foreign keys must be enabled")
    positions = [entry.position for entry in extraction.entries]
    if len(positions) != len(set(positions)):
        raise ValueError("duplicate entry positions")
    list_id = _key(policy.id, edition)
    doc_id = _key(policy.id, extraction.source_url, extraction.content_sha256)
    revision_id = _key(list_id, doc_id, extraction.parser_revision)
    run_id = _key(revision_id, "run")
    observations = _observations(extraction, policy, list_id, revision_id, run_id)
    original = getattr(extraction, "original_url", extraction.source_url)
    reason = getattr(extraction, "review_reason", "Manual transcription requires independent audit")
    rank_semantics = (
        "winner ranked; remaining entries unranked"
        if isinstance(extraction, nbr_2023.Extraction)
        else "unranked; display order is not rank"
    )
    output_hash = sha256(
        json.dumps(asdict(extraction), sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    with _savepoint(db):
        _ensure_source(db, policy)
        db.execute(
            "INSERT INTO source_run (id,source_id,started_at,outcome,parser_version) VALUES (?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
            (run_id, policy.id, accessed_at, "success", extraction.parser_revision),
        )
        db.execute(
            "INSERT INTO source_document VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
            (
                doc_id,
                policy.id,
                extraction.source_url,
                extraction.content_sha256,
                accessed_at,
                None,
                "success",
                policy.retention,
            ),
        )
        db.execute(
            "INSERT INTO published_list (id,source_id,edition,eligibility,rank_semantics,completeness,lineage) VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
            (
                list_id,
                policy.id,
                edition,
                extraction.eligibility,
                rank_semantics,
                extraction.ballot_completeness,
                extraction.lineage,
            ),
        )
        _check_list(
            db,
            list_id,
            (
                extraction.eligibility,
                rank_semantics,
                extraction.ballot_completeness,
                extraction.lineage,
            ),
        )
        exists = db.execute(
            "SELECT 1 FROM extraction_revision WHERE id=?", (revision_id,)
        ).fetchone()
        _check_output(db, revision_id, output_hash, exists is not None)
        if exists:
            return revision_id
        db.execute(
            "INSERT INTO extraction_revision VALUES (?,?,?,?,?,?,?,?)",
            (
                revision_id,
                policy.id,
                list_id,
                doc_id,
                run_id,
                extraction.parser_revision,
                "provisional",
                "pending",
            ),
        )
        db.execute("INSERT INTO extraction_fingerprint VALUES (?,?)", (revision_id, output_hash))
        db.execute(
            "INSERT INTO extraction_detail VALUES (?,?,?,?,?)",
            (
                revision_id,
                extraction.document_revision,
                original,
                extraction.extraction_scope,
                reason,
            ),
        )
        _store_entries(db, observations)
    return revision_id
