"""Synthetic permitted offers; no real provider policy or account entitlement."""

from datetime import UTC, datetime, timedelta

from film_iq.availability.assertion import Assertion
from film_iq.availability.fetch import Fetch
from film_iq.availability.opportunity import Opportunity
from film_iq.availability.policies import record_policy
from film_iq.retention import CachePolicy

NOW = datetime(2026, 1, 1, tzinfo=UTC)
EXPIRY = NOW + timedelta(days=30)


def policy(source="fixture", **changes):
    return CachePolicy(
        source,
        rights_evidence="Synthetic test permission only",
        attribution="Fixture source",
        expires_at=EXPIRY,
        **changes,
    )


def prepare(db, source="fixture"):
    db.commit()
    record_policy(db, policy(source, allowed=True), NOW)


def fetch(day=0, *, source="fixture", status="complete", present=True, plan="Standard"):
    checked = NOW + timedelta(days=day)
    offer = Opportunity(1, "Fixture cinema", "subscription", "US", plan=plan)
    assertions = (
        (Assertion(offer, source, checked, "https://example.test/film", work_status="reviewed"),)
        if present
        else ()
    )
    return Fetch(source, 1, "US", checked, status, assertions, plan, True)
