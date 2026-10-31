"""Synthetic accepted award-category cohorts may legitimately repeat one work."""

from dataclasses import replace

from recognition_support import NOW, REVIEW
from test_curated_csv import MANIFEST, body

from film_iq.ingest.accept import accept
from film_iq.ingest.audit import AuditAttestation
from film_iq.ingest.curated import import_list
from film_iq.recognition.models import AwardOutcome
from film_iq.recognition.storage import classify_entry


def award_cohort(db, edition):
    source = body(
        edition=edition,
        rank="",
        tie="",
        raw_title="Fixture repeated film",
        tmdb_id="123",
        identity_reviewer="fixture reviewer",
        identity_evidence="synthetic repeated-work identity",
    )
    manifest = replace(MANIFEST, edition=edition, evidence_kind="unknown")
    imported = import_list(source, manifest, db=db, accessed_at=NOW)
    revision = imported["revision_id"]
    rows = db.execute(
        "SELECT entry_id,position FROM entry_observation WHERE revision_id=? ORDER BY position",
        (revision,),
    )
    for entry, position in rows:
        award = AwardOutcome(
            "Fixture festival",
            edition,
            f"Category {edition}-{position}",
            "prize",
            recipient=f"Fixture recipient {position}",
            recipient_kind="person",
        )
        classify_entry(db, entry, revision, award, REVIEW)
    accept(
        db,
        revision,
        AuditAttestation(REVIEW.auditor, REVIEW.evidence, NOW, True, True, 3),
        previous_revision_id=None,
    )
    return imported
