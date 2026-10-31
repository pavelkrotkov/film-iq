"""Choices expose price, exact source expiry and conservative last day separately."""

from test_report_runtime import assertion, report_inputs, setup_db

from film_iq.report import build_report
from film_iq.report_render import markdown


def test_rental_price_and_source_expiry_survive_actual_assertion_report(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    item = assertion(price_minor=499, asserted_expires_at="2026-11-10T12:00:00+00:00")
    item["opportunity"]["kind"] = "rent"
    data["assertions"] = [item]
    output = markdown(build_report(evidence_db, data))
    assert "one-off rental price USD 4.99" in output
    assert "last full viewing day 2026-11-09" in output
    assert "provider-asserted expiry 2026-11-10 12:00:00+00:00" in output
    assert "prices and entitlement unverified" not in output


def test_unknown_terms_remain_unknown(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    data["assertions"] = [assertion(price_minor=None)]
    output = markdown(build_report(evidence_db, data))
    assert "access price unknown" in output
    assert "last full viewing day unknown; provider-asserted expiry unknown" in output
    assert "entitlement unconfirmed" in output
