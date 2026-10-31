"""Classification cannot grant itself source rights or infer legacy evidence type."""

import pytest
from recognition_support import NOW
from test_scoring_a1 import accepted

from film_iq.recognition import components
from film_iq.recognition.review import ClassificationReview
from film_iq.scoring.a1 import load_evidence
from film_iq.storage import migrate


@pytest.mark.parametrize(
    "independent,allowed", [(False, True), (True, False), (1, True), (True, "allowed")]
)
def test_review_requires_exact_independent_and_allowed_assertions(independent, allowed):
    with pytest.raises(ValueError):
        ClassificationReview(
            "Fixture reviewer", "Audit", NOW, independent, allowed, "Fixture rights", "Test"
        )


def test_schema_ten_upgrade_keeps_legacy_unknown(evidence_db):
    accepted(evidence_db)
    evidence_db.execute("UPDATE film_index SET tmdb_id=123")
    evidence_db.commit()
    evidence_db.executescript(
        "DROP TABLE recognition_snapshot; DROP TABLE entry_recognition; PRAGMA user_version=10;"
    )
    migrate(evidence_db)
    assert evidence_db.execute("SELECT count(*) FROM entry_recognition").fetchone() == (0,)
    assert load_evidence(evidence_db) == []
    assert len(components(evidence_db, 123)["unclassified"]) == 1
    assert evidence_db.execute("PRAGMA foreign_key_check").fetchall() == []
