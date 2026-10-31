"""Accepted source/identity gates feed separate components without critic inflation."""

from typing import cast

import pytest
from recognition_support import REVIEW, accepted_component

from film_iq.recognition import components
from film_iq.recognition.models import AwardOutcome, Selection
from film_iq.recognition.review import ClassificationReview
from film_iq.recognition.storage import classify_entry, declare_selection
from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence


@pytest.mark.parametrize("kind", ["registry_selection", "institutional_selection"])
def test_accepted_institutional_source_never_becomes_a_critic(evidence_db, kind):
    accepted_component(evidence_db, Selection(kind, "Fixture selection", "2025"))
    assert score(load_evidence(evidence_db)) == ()
    result = components(evidence_db, 123)
    assert len(result[kind]) == 1 and "critic_selection" in result["missing"]
    assert result[kind][0]["url"] == "https://example.test/list"


def test_award_recipient_and_multiple_reception_measures_roundtrip(evidence_db):
    award = AwardOutcome(
        "Fixture award",
        "2025",
        "Best Actor",
        "prize",
        recipient="Fixture Person",
        recipient_kind="person",
    )
    accepted_component(evidence_db, award)
    result = components(evidence_db, 123)
    assert result["award_outcome"][0]["component"][0]["recipient_kind"] == "person"
    assert "reception_metric" in result["missing"]
    assert not load_evidence(evidence_db)


def test_legacy_requires_independent_review_and_known_reclassification_is_immutable(evidence_db):
    selection = Selection("registry_selection", "Fixture", "2025")
    with pytest.raises(ValueError, match="explicit classification review"):
        declare_selection(evidence_db, "entry", "rev", selection)
    classify_entry(evidence_db, "entry", "rev", selection, REVIEW)
    before = evidence_db.total_changes
    classify_entry(evidence_db, "entry", "rev", selection, REVIEW)
    assert evidence_db.total_changes == before
    with pytest.raises(ValueError, match="new revision"):
        classify_entry(
            evidence_db, "entry", "rev", Selection("critic_selection", "Fixture", "2025"), REVIEW
        )
    with pytest.raises(ValueError, match="independent"):
        classify_entry(evidence_db, "entry", "rev", selection, cast(ClassificationReview, None))
