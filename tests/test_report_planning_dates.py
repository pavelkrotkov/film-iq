"""Assessment-anchored scheduling rejects impossible past slots, preserving backtests."""

import pytest
from test_report import inputs
from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report


@pytest.mark.parametrize("factory", [inputs, report_inputs])
def test_report_rejects_slots_before_its_declared_assessment(evidence_db, factory):
    setup_db(evidence_db)
    data = factory()
    data["dates"] = ["2026-10-01"]
    if "assertions" in data:
        data["assertions"][0]["asserted_added_on"] = "2026-10-28T00:00:00+00:00"
    with pytest.raises(ValueError, match="on or after the assessment"):
        build_report(evidence_db, data)


def test_same_day_historical_assessment_is_not_compared_to_wall_clock(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    data["checked_at"] = "2020-01-01T12:00:00+00:00"
    data["assessed_at"] = "2020-01-01T13:00:00+00:00"
    data["dates"] = ["2020-01-01"]
    data["assertions"] = [
        assertion(
            checked_at=data["checked_at"],
            asserted_added_on="2020-01-01T12:30:00+00:00",
            asserted_expires_at="2020-01-02T00:00:00+00:00",
        )
    ]
    report = build_report(evidence_db, data)
    assert report["verified_plans"][0]["choices"][0]["viewing_date"].isoformat() == "2020-01-01"


def test_known_future_arrival_does_not_become_current_access(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    data["assertions"] = [assertion(asserted_added_on="2026-10-30T00:00:00+00:00")]
    report = build_report(evidence_db, data)
    assert all(not plan["choices"] for plan in report["plans"])
