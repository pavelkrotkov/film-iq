"""Source provenance survives cross-provider opportunity deduplication."""

from offer_store_support import NOW, fetch, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.availability.state import current_opportunities


def test_opportunity_dedup_keeps_both_source_assertions(evidence_db):
    prepare(evidence_db)
    prepare(evidence_db, "second")
    save_fetch(evidence_db, fetch(), NOW)
    save_fetch(evidence_db, fetch(source="second"), NOW)
    grouped = current_opportunities(evidence_db, NOW)
    assert len(grouped) == 1
    assert {item.source for item in next(iter(grouped.values()))} == {"fixture", "second"}
