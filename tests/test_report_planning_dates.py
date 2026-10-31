"""Assessment-anchored scheduling rejects impossible past slots, preserving backtests."""

from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report


def test_known_future_arrival_does_not_become_current_access(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    data["assertions"] = [assertion(asserted_added_on="2026-10-30T00:00:00+00:00")]
    report = build_report(evidence_db, data)
    assert all(not plan["choices"] for plan in report["plans"])
