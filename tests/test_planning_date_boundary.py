"""Calendar dates follow the declared assessment offset; no invented wall clock."""

from datetime import date

import pytest

from film_iq.planning.report_dates import planning_dates


def test_same_day_slot_uses_assessment_timezone_even_across_utc_midnight():
    inputs = {
        "assessed_at": "2020-01-02T00:30:00+14:00",
        "checked_at": "2020-01-01T10:00:00Z",
        "dates": ["2020-01-02"],
    }
    assert planning_dates(inputs) == [date(2020, 1, 2)]
    inputs["dates"] = ["2020-01-01"]
    with pytest.raises(ValueError, match="assessment calendar day"):
        planning_dates(inputs)


def test_naive_assessment_cannot_anchor_a_plan():
    with pytest.raises(ValueError, match="timezone-aware"):
        planning_dates({"checked_at": "2020-01-01T10:00:00", "dates": ["2020-01-01"]})
