"""Pending and identity history use existing SQL contracts."""

from dataclasses import replace

from test_curated_csv import MANIFEST, body

from film_iq.ingest.accept import accept
from film_iq.ingest.audit import AuditAttestation
from film_iq.ingest.curated import import_list

NOW = "2026-10-30T00:00:00Z"


def test_reimport_correction_and_acceptance(evidence_db):
    db = evidence_db
    first = import_list(body(), MANIFEST, db=db, accessed_at=NOW)
    assert import_list(body(), MANIFEST, db=db, accessed_at=NOW) == first
    revision = first["revision_id"]
    audit = AuditAttestation("independent fixture reviewer", "synthetic audit", NOW, True, True, 3)
    accept(db, revision, audit, previous_revision_id=None)
    changed = import_list(
        body(director="Corrected fixture director"), MANIFEST, db=db, accessed_at=NOW
    )
    assert changed["revision_id"] != revision
    assert db.execute(
        "SELECT revision_id FROM current_extraction WHERE revision_id=?", (revision,)
    ).fetchone() == (revision,)
    assert db.execute(
        "SELECT count(*) FROM entry_observation WHERE revision_id=?", (revision,)
    ).fetchone() == (3,)
    assert db.execute(
        "SELECT director FROM entry_observation WHERE revision_id=? LIMIT 1", (revision,)
    ).fetchone() == (None,)


def test_reviewed_identity_is_idempotent_and_watched_excluded(evidence_db):
    db = evidence_db
    # A one-entry scope avoids asserting three source entries are the same work.
    single = (
        "\n".join(
            body(
                tmdb_id="123",
                identity_reviewer="fixture auditor",
                identity_evidence="synthetic crosswalk",
            ).splitlines()[:2]
        )
        + "\n"
    )
    manifest = replace(MANIFEST, expected_count=1)
    result = import_list(
        single, manifest, db=db, accessed_at=NOW, watched_tmdb_ids=frozenset({123})
    )
    assert result["watched_excluded"] == 1
    assert result["accepted"] == 0
    assert result["reviewed_identities"] == 1
    import_list(single, manifest, db=db, accessed_at=NOW)
    assert db.execute("SELECT count(*) FROM current_match").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM match_decision").fetchone() == (1,)


def test_derivative_keeps_independence_lineage(evidence_db):
    derivative = replace(MANIFEST, lineage="derivative of person-a ballot")
    result = import_list(body(), derivative, db=evidence_db, accessed_at=NOW)
    assert result["lineage"] == "derivative of person-a ballot"
    assert evidence_db.execute(
        "SELECT independence_group FROM source WHERE id='critic'"
    ).fetchone() == ("person-a",)
