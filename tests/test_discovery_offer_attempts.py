"""Unknown tiers and partial positives remain visible without negative inference."""

from datetime import timedelta

import pytest
from discovery_offer_support import configure, import_observation, observation, report
from offer_store_support import NOW, prepare


@pytest.mark.parametrize("status", ["complete", "partial"])
def test_positive_unknown_plan_claims_are_exploratory_not_comparison_baselines(
    evidence_db, tmp_path, status
):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    import_observation(tmp_path, observation(status=status, plan=None))
    result = report(tmp_path)
    state = result["candidates"][0]["offer_states"][0]
    assert state["current"] is None
    assert state["latest_attempt"]["assertions"][0]["opportunity"]["plan"] is None
    assert "Fixture cinema" in report(tmp_path, output_format="markdown")


@pytest.mark.parametrize("status", ["partial", "unknown"])
def test_failed_or_partial_latest_does_not_freshen_or_remove_previous_baseline(
    evidence_db, tmp_path, status
):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    import_observation(tmp_path, observation())
    import_observation(tmp_path, observation(1, status=status, present=False))
    result = report(tmp_path, NOW + timedelta(days=1))
    state = result["candidates"][0]["offer_states"][0]
    assert state["current"]["checked_at"] == NOW.isoformat()
    assert len(state["current"]["assertions"]) == 1
    assert state["latest_attempt"]["status"] == status
    output = report(tmp_path, NOW + timedelta(days=1), "markdown")
    assert "Previously reported" in output and "2026-01-01 00:00 UTC" in output
    assert "Latest check" in output
