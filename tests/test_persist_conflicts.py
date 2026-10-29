from dataclasses import replace
from pathlib import Path

import pytest

from film_iq.ingest.adapters import nbr_2023
from film_iq.ingest.persist import SourcePolicy, persist

FIXTURES = Path(__file__).parent / "fixtures/ingest"
POLICY = SourcePolicy(
    "nbr",
    "NBR",
    "https://nationalboardofreview.org/",
    "awards",
    "nbr",
    "public",
    "metadata",
    "none",
    "cite",
)


@pytest.mark.parametrize("change", ["title", "missing", "scope", "review"])
def test_same_revision_rejects_changed_output(evidence_db, change):
    db = evidence_db
    result = nbr_2023.extract((FIXTURES / "nbr-2023.wiki").read_bytes())
    rev = persist(db, result, POLICY, "2023", "now")
    changes = {
        "title": replace(
            result, entries=(replace(result.entries[0], title="changed"), *result.entries[1:])
        ),
        "missing": replace(result, entries=result.entries[:-1]),
        "scope": replace(result, extraction_scope="changed"),
        "review": replace(result, review_status="changed"),
    }
    before = db.execute(
        "SELECT * FROM entry_observation WHERE revision_id=? ORDER BY position", (rev,)
    ).fetchall()
    with pytest.raises(ValueError, match="extraction output"):
        persist(db, changes[change], POLICY, "2023", "later")
    assert (
        db.execute(
            "SELECT * FROM entry_observation WHERE revision_id=? ORDER BY position", (rev,)
        ).fetchall()
        == before
    )


@pytest.mark.parametrize("field", ["eligibility", "ballot_completeness", "lineage"])
def test_changed_list_metadata_rolls_back_new_revision(evidence_db, field):
    db = evidence_db
    result = nbr_2023.extract((FIXTURES / "nbr-2023.wiki").read_bytes())
    persist(db, result, POLICY, "2023", "now")
    counts = [
        db.execute(f"SELECT count(*) FROM {table}").fetchone()
        for table in ("source_run", "source_document", "extraction_revision")
    ]
    changed = replace(result, parser_revision="2", **{field: "changed"})
    with pytest.raises(ValueError, match="published list metadata"):
        persist(db, changed, POLICY, "2023", "later")
    assert [
        db.execute(f"SELECT count(*) FROM {table}").fetchone()
        for table in ("source_run", "source_document", "extraction_revision")
    ] == counts


def test_revision_without_fingerprint_fails_closed(evidence_db):
    db = evidence_db
    result = nbr_2023.extract((FIXTURES / "nbr-2023.wiki").read_bytes())
    rev = persist(db, result, POLICY, "2023", "now")
    db.execute("DELETE FROM extraction_fingerprint WHERE revision_id=?", (rev,))
    db.commit()
    with pytest.raises(ValueError, match="cannot be verified"):
        persist(db, result, POLICY, "2023", "later")
