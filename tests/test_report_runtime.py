"""The public report joins current personal data and qualified source assertions."""

import pytest
from test_report import inputs
from test_scoring_a1 import accepted

from film_iq.report import build_report


def assertion(**changes):
    return {
        "provider_id": 7,
        "opportunity": {"film_id": 1, "service": "Fixture", "kind": "free", "country": "US"},
        "source": "official-test",
        "checked_at": "2026-10-29T12:00:00+00:00",
        "url": "https://example.test/film",
        "price_minor": 0,
        "currency": "USD",
        "entitlement": "confirmed",
        "work_status": "reviewed",
        **changes,
    }


def report_inputs():
    return {
        **inputs(),
        "assertions": [assertion()],
        "assessed_at": "2026-10-29T13:00:00+00:00",
        "offer_max_age_hours": 24,
        "utility_power": 2,
    }


def setup_db(db):
    accepted(db)
    db.execute("UPDATE film_index SET tmdb_id=1")
    db.commit()


def test_assertions_produce_separate_verified_plan_and_preserve_source(evidence_db):
    setup_db(evidence_db)
    data = report_inputs()
    result = build_report(evidence_db, data)
    assert result["verified_plans"][0]["choices"][0]["film"]["id"] == 1
    assert result["assertions"][0]["source"] == "official-test"
    assert "power=2" in result["plans"][0]["assumptions"]
    data["assertions"] = [assertion(entitlement="unconfirmed")]
    result = build_report(evidence_db, data)
    assert result["plans"][0]["feasibility"] == "tentative"
    assert not result["verified_plans"][0]["choices"]


@pytest.mark.parametrize(
    "change",
    [
        {"checked_at": "2026-10-20T12:00:00+00:00"},
        {"work_status": "unresolved"},
        {"asserted_expires_at": "2026-10-29T12:30:00+00:00"},
        {"currency": "EUR"},
    ],
)
def test_stale_unresolved_expired_foreign_currency_cannot_enter_plan(evidence_db, change):
    setup_db(evidence_db)
    data = report_inputs()
    data["assertions"] = [assertion(**change)]
    result = build_report(evidence_db, data)
    assert all(not plan["choices"] for plan in result["plans"])
