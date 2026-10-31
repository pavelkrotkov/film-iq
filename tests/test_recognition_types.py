"""Unlike metrics, award subjects and unknowns cannot be silently conflated."""

from datetime import date

import pytest

from film_iq.recognition.models import AwardOutcome, ReceptionMetric


def test_original_units_unknowns_and_person_prizes_stay_distinct():
    metric = ReceptionMetric("Fixture mean", "critics", "mean", None, "score_100", None)
    assert metric.value is metric.sample_count is None
    grade = ReceptionMetric("Fixture grade", "audience", "grade", "A-", "grade")
    assert grade.value == "A-" and grade.sample_count is None
    award = AwardOutcome(
        "Fixture Academy",
        None,
        "Best Actor",
        "prize",
        recipient="Fixture Person",
        recipient_kind="person",
    )
    assert award.edition is award.effective_on is None
    assert award.recipient_kind == "person" and award.category != "Best Film"
    with pytest.raises(ValueError):
        ReceptionMetric("Fixture mean", "critics", "mean", 8.5, "percent")
    with pytest.raises(ValueError):
        AwardOutcome(
            "Fixture", "2025", "Film", "prize", effective_on=date(2025, 1, 1), recipient="Person"
        )
