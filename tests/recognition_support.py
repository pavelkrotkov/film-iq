"""Entirely synthetic typed source facts, audits and reviewed work identities."""

from dataclasses import replace

from test_curated_csv import MANIFEST, body

from film_iq.ingest.accept import accept
from film_iq.ingest.audit import AuditAttestation
from film_iq.ingest.curated import import_list
from film_iq.recognition.review import ClassificationReview
from film_iq.recognition.storage import classify_entry

NOW = "2026-10-31T00:00:00Z"
REVIEW = ClassificationReview(
    "independent fixture reviewer",
    "synthetic component audit",
    NOW,
    True,
    True,
    "synthetic fixture rights",
    "local test",
)


def accepted_component(db, component):
    single = (
        "\n".join(
            body(
                tmdb_id="123",
                identity_reviewer="fixture reviewer",
                identity_evidence="synthetic work identity",
            ).splitlines()[:2]
        )
        + "\n"
    )
    result = import_list(
        single, replace(MANIFEST, expected_count=1, evidence_kind="unknown"), db=db, accessed_at=NOW
    )
    revision = result["revision_id"]
    entry = db.execute(
        "SELECT entry_id FROM entry_observation WHERE revision_id=?", (revision,)
    ).fetchone()[0]
    classify_entry(db, entry, revision, component, REVIEW)
    accept(
        db,
        revision,
        AuditAttestation(REVIEW.auditor, REVIEW.evidence, NOW, True, True, 1),
        previous_revision_id=None,
    )
    db.execute("UPDATE source SET independence_verification='verified' WHERE id='critic'")
    db.execute(
        "UPDATE published_list SET lineage_kind='original',lineage_verification='verified' WHERE source_id='critic'"
    )
    return revision, entry
