"""Unlike metrics, award subjects and unknowns cannot be silently conflated."""

from datetime import date

import pytest

from film_iq.recognition.models import AwardOutcome, ReceptionMetric


@pytest.mark.parametrize("value", [True, False, "85", float("nan"), float("inf"), -1, 101])
def test_positivity_rejects_boolean_strings_nonfinite_and_out_of_range(value):
    with pytest.raises(ValueError):
        ReceptionMetric("Fixture positivity", "critics", "positivity", value, "percent")


@pytest.mark.parametrize("sample", [True, 4.5, "10", -1])
def test_sample_counts_are_explicit_integer_observations(sample):
    with pytest.raises(ValueError):
        ReceptionMetric("Fixture mean", "critics", "mean", 8.5, "score_10", sample)


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
