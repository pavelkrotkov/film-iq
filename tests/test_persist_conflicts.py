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


def test_same_revision_rejects_changed_output(evidence_db):
    change = "title"
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
