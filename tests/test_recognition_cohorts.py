"""Release views use reviewed dates and never replace source-listed years."""

from discovery_fixtures import accept_source, cohort, fresh_status, snapshot
from display_fixtures import NOW, catalog_path

from film_iq.discovery import build_discovery
from film_iq.discovery_presentation import present_discovery
from film_iq.recognition.snapshot import replay, save


def test_reviewed_catalog_release_cohort_keeps_source_year_unknown(evidence_db, tmp_path):
    accept_source(evidence_db)
    raw = build_discovery(cohort(), snapshot(), db=evidence_db, refresh_status=fresh_status())
    report = present_discovery(raw, catalog_path(tmp_path), now=NOW)
    pick = report["suggested_unwatched"][0]
    assert pick["release_cohort"]["source_listed_year"] is None
    assert pick["release_cohort"]["catalog_release_year"] == 2025
    assert pick["release_cohort"]["catalog_evidence"]
    assert report["release_cohorts"]["reviewed_catalog_years"] == {"2025": [123]}
    identifier = save(evidence_db)
    component = replay(evidence_db, identifier)["components"][0]
    assert component["listed_year"] is component["catalog_release_year"] is None
    assert "eligibility" in component and "family" in component
