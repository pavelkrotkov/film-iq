"""Local human-readable changes preserve the source-specific meaning."""

from datetime import timedelta

from offer_store_support import NOW, fetch, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.changes import digest
from film_iq.changes_render import markdown


def test_offer_addition_and_absence_are_source_specific(evidence_db):
    prepare(evidence_db)
    _, baseline = digest(evidence_db, None, NOW)
    save_fetch(evidence_db, fetch(), NOW)
    save_fetch(evidence_db, fetch(1, present=False), NOW + timedelta(days=1))
    result, _ = digest(evidence_db, baseline, NOW + timedelta(days=1))
    result["acknowledgement"] = "preview; not acknowledged"
    output = markdown(result)
    assert "Newly observed offer" in output
    assert "Offer absent from complete source snapshot" in output
    assert output.count("TMDB 1, Fixture cinema / Standard (fixture)") == 2
    assert "preview; not acknowledged" in output
