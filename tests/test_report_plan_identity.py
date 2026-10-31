"""Service IDs cannot erase exact plan identity or price evidence."""

import pytest
from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report


def test_exact_plan_identity_and_subscription_price_are_enforced(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    subscription = {
        "film_id": 1,
        "service": "Fixture",
        "kind": "subscription",
        "country": "US",
        "plan": "Standard",
    }
    data["assertions"] = [assertion(opportunity=subscription, price_minor=500)]
    data["service_prices_cents"] = {"7": 400}
    with pytest.raises(ValueError, match="subscription fee"):
        build_report(evidence_db, data)
    data["service_prices_cents"] = {"7": 500}
    data["assertions"].append(
        assertion(opportunity={**subscription, "plan": "Premium"}, price_minor=500)
    )
    with pytest.raises(ValueError, match="different services, tiers"):
        build_report(evidence_db, data)
