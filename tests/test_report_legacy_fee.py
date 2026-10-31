"""Legacy caller subscription fees remain separate from unknown provider prices."""

import pytest
from test_report import inputs
from test_report_runtime import setup_db

from film_iq.report import build_report
from film_iq.report_render import markdown


def legacy_subscription():
    data = inputs()
    data["offers"]["1"]["results"]["US"] = {
        "link": "https://example.test/subscribe",
        "flatrate": [{"provider_id": 7, "provider_name": "Fixture"}],
    }
    return data


@pytest.mark.parametrize("key", [7, "7"])
def test_known_legacy_caller_fee_is_shown_without_inventing_source_price(evidence_db, key):
    setup_db(evidence_db)
    data = legacy_subscription()
    data["service_prices_cents"] = {key: 500}
    report = build_report(evidence_db, data)
    plan = next(plan for plan in report["plans"] if plan["option"] == "service 7")
    assert plan["cost_cents"] == 500 and plan["choices"][0]["offer"]["price_cents"] is None
    assert report["service_price_assumptions"] == {"7": 500}
    assert "caller-declared subscription fee assumption USD 5.00" in markdown(report)
    assert plan["feasibility"] == "tentative"


def test_unknown_existing_legacy_fee_stays_unknown_and_sunk(evidence_db):
    setup_db(evidence_db)
    data = legacy_subscription()
    data["current_services"] = [7]
    report = build_report(evidence_db, data)
    assert report["plans"][0]["cost_cents"] == 0
    assert "subscription fee assumption unknown (existing fees are sunk" in markdown(report)
