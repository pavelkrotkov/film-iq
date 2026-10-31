"""Provider expiry is converted to the declared viewing calendar, not relabelled."""

from datetime import datetime, timedelta

import pytest
from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report
from film_iq.report_render import markdown


@pytest.mark.parametrize(
    "assessment,expiry,last_day,day,eligible",
    [
        ("2026-10-29T13:00:00-04:00", "2026-11-01T00:00:00Z", "2026-10-30", "2026-10-30", True),
        ("2026-10-29T13:00:00-04:00", "2026-11-01T00:00:00Z", "2026-10-30", "2026-10-31", False),
    ],
)
def test_expiry_uses_assessment_calendar_but_source_timestamp_survives(
    evidence_db, assessment, expiry, last_day, day, eligible
):
    setup_db(evidence_db)
    data = report_inputs()
    checked = (datetime.fromisoformat(assessment) - timedelta(hours=1)).isoformat()
    data.update(
        assessed_at=assessment,
        dates=[day],
        assertions=[assertion(checked_at=checked, asserted_expires_at=expiry)],
    )
    report = build_report(evidence_db, data)
    choices = report["verified_plans"][0]["choices"]
    assert bool(choices) is eligible
    assert report["assertions"][0]["asserted_expires_at"] == datetime.fromisoformat(expiry)
    if choices:
        output = markdown(report)
        assert f"last full viewing day {last_day}" in output
        assert f"provider-asserted expiry {datetime.fromisoformat(expiry)}" in output
