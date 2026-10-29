"""Persist provisional adapter output without promoting it to accepted evidence."""

import json
import sqlite3
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
    list_id = _key(policy.id, edition)
    doc_id = _key(policy.id, extraction.source_url, extraction.content_sha256)
    revision_id = _key(list_id, doc_id, extraction.parser_revision)
    run_id = _key(revision_id, "run")
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
    with db:
        _ensure_source(db, policy, original)
        db.execute(
            "INSERT OR IGNORE INTO source_run (id,source_id,started_at,outcome,parser_version) VALUES (?,?,?,?,?)",
            (run_id, policy.id, accessed_at, "success", extraction.parser_revision),
        )
        db.execute(
            "INSERT OR IGNORE INTO source_document VALUES (?,?,?,?,?,?,?,?)",
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
            "INSERT OR IGNORE INTO published_list (id,source_id,edition,eligibility,rank_semantics,completeness,lineage) VALUES (?,?,?,?,?,?,?)",
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
        db.execute(
            "INSERT OR IGNORE INTO extraction_revision VALUES (?,?,?,?,?,?,?,?)",
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
        if not exists:
            db.execute(
                "INSERT INTO extraction_fingerprint VALUES (?,?)", (revision_id, output_hash)
            )
        db.execute(
            "INSERT OR IGNORE INTO extraction_detail VALUES (?,?,?,?,?)",
            (
                revision_id,
                extraction.document_revision,
                original,
                extraction.extraction_scope,
                reason,
            ),
        )
        for entry in extraction.entries:
            entry_id = _key(list_id, str(entry.position))
            db.execute(
                "INSERT OR IGNORE INTO list_entry VALUES (?,?,?,?)",
                (entry_id, policy.id, list_id, str(entry.position)),
            )
            context = (
                getattr(entry, "raw_context", f"{entry.title} ({entry.release_date})")
                if isinstance(entry, film_registry.Entry)
                else entry.raw_context
            )
            db.execute(
                "INSERT OR IGNORE INTO entry_observation (entry_id,source_id,list_id,revision_id,raw_title,raw_context,position,rank,tie,locator,extraction_decision) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    entry_id,
                    policy.id,
                    list_id,
                    revision_id,
                    entry.title,
                    context,
                    entry.position,
                    entry.rank,
                    None,
                    entry.locator,
                    "pending",
                ),
            )
    return revision_id
