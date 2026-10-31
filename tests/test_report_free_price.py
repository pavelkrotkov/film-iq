"""Contradictory source costs fail visibly before planner filtering."""

import pytest
from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report


def test_positive_free_assertion_is_not_silently_dropped(evidence_db):
    kind, currency = "free", "USD"
    setup_db(evidence_db)
    data = report_inputs()
    item = assertion(price_minor=999, currency=currency)
    item["opportunity"]["kind"] = kind
    data["assertions"] = [item]
    data["budget_cents"] = 0
    with pytest.raises(ValueError, match="free/ads access price"):
        build_report(evidence_db, data)
