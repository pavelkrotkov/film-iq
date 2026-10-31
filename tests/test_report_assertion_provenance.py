"""A selected qualified assertion must retain its own link, source and timestamp."""

from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report
from film_iq.report_render import markdown


def test_excluded_assertion_cannot_supply_verified_plan_citation(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    fresh = assertion(
        source="fresh-official",
        url="https://example.test/qualified",
        asserted_expires_at="2026-11-30T00:00:00+00:00",
    )
    stale = assertion(
        source="stale-decoy",
        url="https://example.test/excluded",
        checked_at="2026-10-20T12:00:00+00:00",
        entitlement="unconfirmed",
    )
    data["assertions"] = [fresh, stale]
    report = build_report(evidence_db, data)
    selected = report["verified_plans"][0]["choices"][0]["offer"]
    assert report["assertions"][selected["assertion_index"]]["source"] == "fresh-official"
    rendered = markdown(report)
    assert "https://example.test/qualified" in rendered and "fresh-official" in rendered
    assert "stale-decoy" not in rendered and "https://example.test/excluded" not in rendered
