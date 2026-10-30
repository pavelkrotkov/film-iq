"""Independent PR review reproductions use synthetic records only."""

import csv
from dataclasses import replace

import pytest
from test_curated_csv import MANIFEST, body

from film_iq.ingest.accept import accept
from film_iq.ingest.audit import AuditAttestation
from film_iq.ingest.curated import import_list
from film_iq.ingest.curated_csv import read_csv

NOW = "2026-10-30T00:00:00Z"


def test_pending_correction_cannot_reattribute_accepted_ballot(evidence_db):
    revision = import_list(body(), MANIFEST, db=evidence_db, accessed_at=NOW)["revision_id"]
    audit = AuditAttestation("independent fixture auditor", "synthetic source", NOW, True, True, 3)
    accept(evidence_db, revision, audit, previous_revision_id=None)
    with pytest.raises(ValueError, match="ballot scope"):
        import_list(
            body(ballot_scope="person-b"),
            replace(MANIFEST, ballot_scope="person-b"),
            db=evidence_db,
            accessed_at=NOW,
        )
    assert evidence_db.execute(
        "SELECT p.author FROM published_list p JOIN current_extraction c ON c.list_id=p.id WHERE c.revision_id=?",
        (revision,),
    ).fetchone() == ("person-a",)
    assert evidence_db.execute(
        "SELECT count(*) FROM extraction_revision WHERE extractor_version='curated-csv-1'"
    ).fetchone() == (1,)


@pytest.mark.parametrize("field", ["identity_reviewer", "identity_evidence"])
def test_whitespace_cannot_establish_reviewed_id(field):
    values = {"tmdb_id": "123", "identity_reviewer": "auditor", "identity_evidence": "crosswalk"}
    values[field] = " \t "
    with pytest.raises(ValueError, match="identity reviewer"):
        read_csv(body(**values))


def test_unterminated_final_quote_rejected_before_persistence(evidence_db):
    truncated = body().rstrip().rsplit(",", 1)[0] + ',"unterminated'
    with pytest.raises(csv.Error, match="unexpected end"):
        import_list(truncated, MANIFEST, db=evidence_db, accessed_at=NOW)
    assert evidence_db.execute("SELECT count(*) FROM source WHERE id='critic'").fetchone() == (0,)
