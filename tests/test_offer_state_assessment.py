"""All shared state consumers withhold later observations before assessment."""

from datetime import timedelta

from offer_store_support import NOW, fetch, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.availability.state import current_opportunities, read_state


def test_future_latest_baseline_and_first_seen_are_not_visible(evidence_db):
    prepare(evidence_db)
    later = NOW + timedelta(days=1)
    save_fetch(evidence_db, fetch(1), later)
    before = read_state(evidence_db, fetch(), NOW)
    assert before == {"latest_attempt": None, "current": None, "events": [], "first_seen_by_us": []}
    assert current_opportunities(evidence_db, NOW) == {}
    assert len(current_opportunities(evidence_db, later)) == 1
