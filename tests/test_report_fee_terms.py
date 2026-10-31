"""Known recurring fees are assumptions counted once, not extra film charges."""

from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report
from film_iq.report_render import markdown


def test_new_subscription_fee_is_reported_once_as_a_plan_assumption(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    item = assertion(price_minor=500)
    item["opportunity"].update(kind="subscription", plan="Exact fixture tier")
    data.update(assertions=[item], service_prices_cents={"7": 500})
    report = build_report(evidence_db, data)
    plan = next(plan for plan in report["verified_plans"] if plan["option"] == "service 7")
    assert plan["cost_cents"] == 500
    output = markdown(report)
    assert "subscription fee assumption USD 5.00" in output
    assert "existing fees are sunk; new-service fee counted once in plan total" in output


def test_current_subscription_fee_remains_sunk(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    item = assertion(price_minor=500)
    item["opportunity"].update(kind="subscription", plan="Existing fixture tier")
    data.update(assertions=[item], current_services=[7])
    report = build_report(evidence_db, data)
    assert report["verified_plans"][0]["cost_cents"] == 0
    assert "subscription fee assumption USD 5.00" in markdown(report)
