"""A type-only correction is pending until explicit source acceptance."""

from dataclasses import replace

from recognition_support import NOW, REVIEW, accepted_component
from test_curated_csv import MANIFEST, body

from film_iq.ingest.accept import accept
from film_iq.ingest.audit import AuditAttestation
from film_iq.ingest.curated import import_list
from film_iq.recognition import components
from film_iq.recognition.models import Selection
from film_iq.scoring.a1 import load_evidence


def test_pending_type_change_preserves_accepted_predecessor(evidence_db):
    previous, _ = accepted_component(
        evidence_db, Selection("registry_selection", "Fixture", "2025")
    )
    source = (
        "\n".join(
            body(
                rank="",
                tie="",
                tmdb_id="123",
                identity_reviewer="fixture reviewer",
                identity_evidence="synthetic work identity",
            ).splitlines()[:2]
        )
        + "\n"
    )
    revised = import_list(
        source,
        replace(MANIFEST, expected_count=1, evidence_kind="critic_selection"),
        db=evidence_db,
        accessed_at=NOW,
    )
    assert revised["revision_id"] != previous
    assert not load_evidence(evidence_db)
    assert len(components(evidence_db, 123)["registry_selection"]) == 1
    accept(
        evidence_db,
        revised["revision_id"],
        AuditAttestation(REVIEW.auditor, REVIEW.evidence, NOW, True, True, 1),
        previous_revision_id=previous,
    )
    assert len(load_evidence(evidence_db)) == 1
    assert components(evidence_db, 123)["registry_selection"] == []
    assert evidence_db.execute(
        "SELECT kind FROM entry_recognition WHERE revision_id=?", (previous,)
    ).fetchone() == ("registry_selection",)
