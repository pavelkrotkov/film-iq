"""Display aliases never change source evidence or establish unreviewed identities."""

from discovery_fixtures import accept_source, cohort, fresh_status, snapshot
from display_fixtures import NOW, catalog_path

from film_iq.discovery import build_discovery
from film_iq.discovery_presentation import present_discovery
from film_iq.discovery_render import markdown


def test_reviewed_display_alias_retains_raw_source_facts(evidence_db, tmp_path):
    accept_source(evidence_db)
    raw = build_discovery(cohort(), snapshot(), db=evidence_db, refresh_status=fresh_status())
    output = present_discovery(raw, catalog_path(tmp_path), "public-support", now=NOW)
    row = output["suggested_unwatched"][0]
    assert (row["raw_title"], row["year"]) == ("Unchanged title", None)
    assert row["display"]["title"] == "Reviewed English title"
    assert "display" not in raw["candidates"][0]
    rendered = markdown(output)
    assert "Reviewed English title" in rendered and "Catalog release: 2025-01-29" in rendered
    assert "Source-listed year: unknown" in rendered and "Unchanged title" in rendered


def test_catalog_never_establishes_a_provisional_work_identity(tmp_path):
    raw = build_discovery(cohort())
    output = present_discovery(raw, catalog_path(tmp_path), now=NOW)
    assert output["candidates"][0]["display"] is None
    assert output["candidates"][0]["identity_status"] == "unresolved"
