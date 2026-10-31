"""Known source facts remain per-entry when a film identity still needs review."""

from discovery_fixtures import cohort, fresh_status, snapshot
from recognition_support import accepted_component

from film_iq.discovery import build_discovery
from film_iq.recognition.models import Selection
from film_iq.recognition.reader import current_components


def test_registry_fact_survives_unresolved_identity_without_merging_unknown_films(evidence_db):
    revision, entry = accepted_component(
        evidence_db, Selection("registry_selection", "Fixture Registry", "2025")
    )
    evidence_db.execute("DELETE FROM current_match WHERE entry_id=?", (entry,))
    output = build_discovery(
        {**cohort(), "revision_id": revision},
        snapshot(),
        db=evidence_db,
        refresh_status=fresh_status(),
    )
    assert output["suggested_unwatched"] == []
    candidate = output["candidates"][0]
    assert candidate["identity_status"] == "unresolved"
    assert len(candidate["public_evidence_components"]["registry_selection"]) == 1
    rows = current_components(evidence_db)
    fact = next(row for row in rows if row["entry_id"] == entry)
    assert fact["tmdb_id"] is fact["match_decision_id"] is None
    assert fact["document_id"]
