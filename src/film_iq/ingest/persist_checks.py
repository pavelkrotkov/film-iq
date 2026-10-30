"""Validation and stable keys for extraction persistence."""

import json
import sqlite3
from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class SourcePolicy:
    id: str
    name: str
    url: str
    family: str
    independence_group: str
    access: str
    retention: str
    redistribution: str
    attribution: str


def _key(*parts: str) -> str:
    return sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


def _check_list(db: sqlite3.Connection, list_id: str, expected: tuple[str, ...]) -> None:
    stored = db.execute(
        "SELECT eligibility,rank_semantics,completeness,lineage FROM published_list WHERE id=?",
        (list_id,),
    ).fetchone()
    if stored != expected:
        raise ValueError("published list metadata differs from existing evidence")


def _check_output(db: sqlite3.Connection, revision_id: str, output_hash: str, exists: bool) -> None:
    if not exists:
        return
    row = db.execute(
        "SELECT output_sha256 FROM extraction_fingerprint WHERE revision_id=?", (revision_id,)
    ).fetchone()
    if row is None or row[0] != output_hash:
        raise ValueError("extraction output differs or cannot be verified for existing revision")


def _ensure_source(db: sqlite3.Connection, policy: SourcePolicy) -> None:
    db.execute(
        "INSERT INTO source (id,name,family,independence_group,url,access_policy,retention_policy,redistribution_policy,attribution) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
        (
            policy.id,
            policy.name,
            policy.family,
            policy.independence_group,
            policy.url,
            policy.access,
            policy.retention,
            policy.redistribution,
            policy.attribution,
        ),
    )
    stored = db.execute(
        "SELECT name,family,independence_group,url,access_policy,retention_policy,redistribution_policy,attribution FROM source WHERE id=?",
        (policy.id,),
    ).fetchone()
    if stored != (
        policy.name,
        policy.family,
        policy.independence_group,
        policy.url,
        policy.access,
        policy.retention,
        policy.redistribution,
        policy.attribution,
    ):
        raise ValueError("source metadata differs from existing policy")
