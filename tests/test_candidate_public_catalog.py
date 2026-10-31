"""A public catalog comparison is independent of account-plan entitlement."""

import json
from datetime import timedelta
from unittest.mock import Mock

import pytest
from candidate_support import WORK, native_payload, permit
from offer_store_support import NOW

from film_iq.availability.candidate_run import run_candidates
from film_iq.availability.fetch import Fetch
from film_iq.availability.state import read_state


def payload(provider, present):
    if provider == "motn":
        return native_payload() if present else native_payload([])
    us = {"link": "https://example.test/watch"}
    if present:
        us["rent"] = [{"provider_id": 7, "provider_name": "Fixture Stream"}]
    return {"id": 123, "results": {"US": us}}


@pytest.mark.parametrize("provider", ["tmdb", "motn"])
def test_two_real_producer_imports_compare_public_presence_not_account_access(
    evidence_db, monkeypatch, provider
):
    permit(evidence_db, provider)
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fixture-secret")
    monkeypatch.setenv("MOVIE_OF_THE_NIGHT_API_KEY", "fixture-secret")
    get = Mock(
        side_effect=[
            (200, json.dumps(payload(provider, present)).encode(), {}) for present in (True, False)
        ]
    )
    for day in (0, 1):
        run_candidates(
            evidence_db,
            provider,
            [WORK],
            max_requests=1,
            live=True,
            now=NOW + timedelta(days=day),
            get=get,
        )
    scope = Fetch(provider, 123, "US", NOW, "unknown", catalog_scope="public_country")
    state = read_state(evidence_db, scope, NOW + timedelta(days=1))
    assert [e["kind"] for e in state["events"]] == ["source_first_seen", "source_absent"]
    assert state["current"]["assertions"] == []
    assert state["current"]["plan_scope"] is None
    assert state["current"]["catalog_scope"] == "public_country"
