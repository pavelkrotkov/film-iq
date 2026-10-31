"""The actual report distinguishes present entitlement from future feasibility."""

import pytest
from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report


@pytest.mark.parametrize(
    "kind,price,option",
    [("free", 0, "no purchase"), ("rent", 300, "rentals"), ("subscription", 500, "service 7")],
)
def test_unknown_expiry_stays_tentative_without_losing_access_fact(
    evidence_db, kind, price, option
):
    setup_db(evidence_db)
    data = report_inputs()
    item = assertion(price_minor=price)
    item["opportunity"].update(kind=kind, plan="Fixture tier")
    data.update(assertions=[item], service_prices_cents={"7": 500})
    report = build_report(evidence_db, data)
    plan = next(p for p in report["plans"] if p["option"] == option)
    verified = next(p for p in report["verified_plans"] if p["option"] == option)
    # Qualified current access remains a fact; only future-plan certainty changes.
    assert (
        plan["feasibility"] == "tentative"
        and plan["choices"][0]["offer"]["entitlement"] == "confirmed"
    )
    assert plan["choices"][0]["offer"]["expires"] is None
    assert not verified["choices"]
    assert report["verified_plans"][0]["cost_cents"] == 0
    assert report["assertions"][0]["asserted_expires_at"] is None


def test_known_departure_allows_last_full_day_but_not_expiry_day(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    data["assertions"] = [assertion(asserted_expires_at="2026-11-02T00:00:00+00:00")]
    report = build_report(evidence_db, data)
    assert report["verified_plans"][0]["feasibility"] == "verified"
    assert report["verified_plans"][0]["choices"][0]["viewing_date"].isoformat() == "2026-11-01"
    data["dates"] = ["2026-11-02"]
    assert not build_report(evidence_db, data)["verified_plans"][0]["choices"]
