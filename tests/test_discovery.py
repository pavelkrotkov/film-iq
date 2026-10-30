"""Accepted evidence, complete personal state and unknown identity stay distinct."""

import json

from discovery_fixtures import accept_source, cohort, snapshot

from film_iq.discovery import build_discovery
from film_iq.discovery_render import markdown


def test_preview_claims_cannot_accept_source_or_suggest_without_database():
    report = build_discovery(cohort(), snapshot(), refresh_status={"stale": False})
    assert (report["accepted"], report["unresolved"]) == (0, 1)
    assert report["suggested_unwatched"] == []
    assert "PRIVATE COMMENT" not in json.dumps(report)


def test_current_acceptance_suggests_only_freshly_unwatched(evidence_db):
    accept_source(evidence_db)
    report = build_discovery(cohort(), snapshot(), db=evidence_db, refresh_status={"stale": False})
    assert (report["accepted"], report["unresolved"], len(report["suggested_unwatched"])) == (
        1,
        0,
        1,
    )
    item = report["candidates"][0]
    assert (item["personal_enjoyment"], item["personal_artistic_merit"], item["merit_status"]) == (
        7,
        None,
        "conflict",
    )
    assert item["external_critical_recognition"] is None
    assert "No purchase" in markdown(report)
    assert build_discovery(cohort(), snapshot(), db=evidence_db)["suggested_unwatched"] == []


def test_watched_scores_remain_visible_and_absent_snapshot_never_guesses(evidence_db):
    accept_source(evidence_db)
    report = build_discovery(
        cohort(), snapshot(True), db=evidence_db, refresh_status={"stale": False}
    )
    assert (report["watched_excluded"], report["suggested_unwatched"]) == (1, [])
    assert report["candidates"][0]["personal_enjoyment"] == 7
    unknown = build_discovery(cohort(), db=evidence_db)
    assert unknown["candidates"][0]["watched"] is None
    assert unknown["suggested_unwatched"] == []
