"""Readable picks lead with films and source reasons; audit metadata stays separate."""

from copy import deepcopy

from discovery_fixtures import accept_source, cohort, fresh_status, snapshot

from film_iq.discovery import build_discovery
from film_iq.discovery_render import markdown


def report(db):
    accept_source(db)
    return build_discovery(cohort(), snapshot(), db=db, refresh_status=fresh_status())


def test_shortlist_leads_with_film_and_reason_before_audit(evidence_db):
    rendered = markdown(report(evidence_db))
    assert rendered.index("## Suggested next") < rendered.index("### [Unchanged title")
    assert rendered.index("Why consider it:") < rendered.index("<details>")
    assert "#2 in [Critic: 2025]" in rendered
    assert "Your ratings: enjoyment 7/10; artistic merit unknown — needs review" in rendered
    assert "| Title | TMDB" not in rendered


def test_one_pick_can_explain_multiple_sources(evidence_db):
    output = report(evidence_db)
    item = output["suggested_unwatched"][0]
    second = {**deepcopy(item), "ballot_scope": "Second critic", "rank": None}
    item["source_reasons"] = [deepcopy(item), second]
    rendered = markdown(output)
    assert "unranked selection in [Second critic: 2025]" in rendered
    assert rendered.count("### [Unchanged title") == 1


def test_watched_and_unresolved_items_stay_visible_outside_suggestions(evidence_db):
    output = report(evidence_db)
    item = output["candidates"][0]
    item["watched"] = True
    output["suggested_unwatched"] = []
    rendered = markdown(output)
    assert "Already watched:" in rendered and "enjoyment 7/10" in rendered
    item["watched"], item["identity_status"] = None, "unresolved"
    assert "Film identity needs review" in markdown(output)
