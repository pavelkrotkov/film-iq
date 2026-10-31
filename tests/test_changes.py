"""Only accepted and permitted durable transitions become local changes."""

from datetime import timedelta

from offer_store_support import NOW, fetch, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.availability.state import read_state, retained_events
from film_iq.changes import digest


def test_baseline_offer_dedup_partial_and_failed_attempts(evidence_db):
    db = evidence_db
    prepare(db)
    first = fetch()
    save_fetch(db, first, NOW)
    result, baseline = digest(db, None, NOW)
    assert result["baseline"] and result["offer_changes"] == []
    assert baseline["offer_events"]
    later = NOW + timedelta(days=1)
    save_fetch(db, fetch(1, status="partial", present=False), later)
    assert digest(db, baseline, later)[0]["offer_changes"] == []
    absent = fetch(2, present=False)
    save_fetch(db, absent, NOW + timedelta(days=2))
    result, acknowledged = digest(db, baseline, NOW + timedelta(days=2))
    assert [e["change"]["kind"] for e in result["offer_changes"]] == ["source_absent"]
    save_fetch(db, absent, NOW + timedelta(days=2))
    assert digest(db, acknowledged, NOW + timedelta(days=2))[0]["offer_changes"] == []
    assert read_state(db, first, later)["events"] == [
        e["change"] for e in retained_events(db, later)
    ]
