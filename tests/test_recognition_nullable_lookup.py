"""Unknown work identities remain distinct entries instead of a shared NULL work."""

from dataclasses import replace

from recognition_support import NOW, REVIEW
from test_curated_csv import MANIFEST, body

from film_iq.ingest.accept import accept
from film_iq.ingest.audit import AuditAttestation
from film_iq.ingest.curated import import_list
from film_iq.recognition import components
from film_iq.recognition.models import Selection
from film_iq.recognition.reader import KINDS, current_components
from film_iq.recognition.snapshot import replay, save
from film_iq.recognition.storage import classify_entry


def test_nullable_public_lookup_never_combines_unresolved_registry_entries(evidence_db):
    imported = import_list(
        body(rank="", tie=""),
        replace(MANIFEST, evidence_kind="unknown"),
        db=evidence_db,
        accessed_at=NOW,
    )
    revision = imported["revision_id"]
    entries = evidence_db.execute(
        "SELECT entry_id FROM entry_observation WHERE revision_id=?", (revision,)
    ).fetchall()
    for (entry,) in entries:
        classify_entry(
            evidence_db,
            entry,
            revision,
            Selection("registry_selection", "Fixture Registry", "2025"),
            REVIEW,
        )
    accept(
        evidence_db,
        revision,
        AuditAttestation(REVIEW.auditor, REVIEW.evidence, NOW, True, True, 3),
        previous_revision_id=None,
    )
    lookup = components(evidence_db, None)
    assert (lookup["registry_selection"], lookup["missing"]) == ([], list(KINDS))
    retained = [row for row in current_components(evidence_db) if row["revision_id"] == revision]
    assert len({(row["entry_id"], row["revision_id"]) for row in retained}) == 3
    frozen = replay(evidence_db, save(evidence_db))
    assert len([row for row in frozen["components"] if row["revision_id"] == revision]) == 3
    assert {row["tmdb_id"] for row in retained} == {None}
