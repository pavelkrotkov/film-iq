"""Review regressions for generation binding and current-revision completeness."""

import pytest
from discovery_fixtures import accept_source, cohort, fresh_status, snapshot

from film_iq.discovery import build_discovery


def test_mismatched_or_missing_status_generation_suppresses_suggestions(evidence_db):
    accept_source(evidence_db)
    status = fresh_status()
    status["last_successful_refresh"] = "2026-10-30T12:00:00+00:00"
    for value in (status, {"stale": False}):
        report = build_discovery(cohort(), snapshot(), db=evidence_db, refresh_status=value)
        assert report["personal_state_stale"] is True
        assert report["suggested_unwatched"] == []
    fresh = build_discovery(cohort(), snapshot(), db=evidence_db, refresh_status=fresh_status())
    assert len(fresh["suggested_unwatched"]) == 1


def test_empty_self_consistent_preview_cannot_hide_current_accepted_entry(evidence_db):
    accept_source(evidence_db)
    selected = cohort()
    selected.update(candidates=[], total_candidates=0)
    with pytest.raises(ValueError, match="complete current accepted revision"):
        build_discovery(selected, db=evidence_db)
