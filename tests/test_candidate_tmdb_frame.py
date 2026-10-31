"""Malformed empty-country frames cannot become source disappearance events."""

import json
from datetime import timedelta
from unittest.mock import Mock

from candidate_support import WORK, permit
from offer_store_support import NOW
from test_candidate_public_catalog import payload

from film_iq.availability.candidate_run import run_candidates
from film_iq.availability.fetch import Fetch
from film_iq.availability.state import read_state


def test_positive_then_malformed_empty_frame_retains_prior_baseline(evidence_db, monkeypatch):
    locator = "not-a-public-url"
    permit(evidence_db, "tmdb")
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fixture-secret")
    malformed = {"id": 123, "results": {"US": {"link": locator}}}
    get = Mock(
        side_effect=[
            (200, json.dumps(payload("tmdb", True)).encode(), {}),
            (200, json.dumps(malformed).encode(), {}),
        ]
    )
    for day in (0, 1):
        run_candidates(
            evidence_db,
            "tmdb",
            [WORK],
            max_requests=1,
            live=True,
            now=NOW + timedelta(days=day),
            get=get,
        )
    scope = Fetch("tmdb", 123, "US", NOW, "unknown", catalog_scope="public_country")
    state = read_state(evidence_db, scope, NOW + timedelta(days=1))
    assert state["current"]["checked_at"] == NOW.isoformat()
    assert state["latest_attempt"]["status"] == "unknown"
    assert [e["kind"] for e in state["events"]] == ["source_first_seen"]
