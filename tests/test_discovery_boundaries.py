"""Read authoritative source fields and reject inconsistent report snapshots."""

import pytest
from discovery_fixtures import accept_source, cohort, snapshot

from film_iq.discovery import build_discovery


def test_stored_rank_wins_over_mutated_preview_and_obsolete_revision_is_pending(evidence_db):
    accept_source(evidence_db)
    changed = cohort()
    changed["candidates"][0]["rank"] = 1
    report = build_discovery(changed, snapshot(), db=evidence_db, refresh_status={"stale": False})
    assert report["candidates"][0]["rank"] == 2
    changed["revision_id"] = "obsolete"
    assert build_discovery(changed, snapshot(), db=evidence_db)["accepted"] == 0


def test_duplicate_snapshot_ids_and_candidate_positions_are_rejected():
    personal = snapshot()
    personal["films"] *= 2
    with pytest.raises(ValueError, match="unique"):
        build_discovery(cohort(), personal)
    selected = cohort()
    selected["candidates"] *= 2
    selected["total_candidates"] = 2
    with pytest.raises(ValueError, match="unique"):
        build_discovery(selected)


def test_bad_scores_are_not_shown_as_valid_personal_judgment():
    personal = snapshot()
    personal["films"][0]["personal_enjoyment"] = 11
    with pytest.raises(ValueError, match="1–10"):
        build_discovery(cohort(), personal)
