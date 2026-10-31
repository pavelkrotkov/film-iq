"""Permission, identity and observation-time guards apply before rendering."""

from dataclasses import replace
from datetime import timedelta

import pytest
from discovery_offer_support import configure, import_observation, observation, report
from offer_store_support import EXPIRY, NOW, policy, prepare

from film_iq.availability.policies import record_policy


@pytest.mark.parametrize("changes", [{"allowed": False}, {"allowed": True, "terminated": True}])
def test_current_permission_denial_hides_all_provider_content(evidence_db, tmp_path, changes):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    import_observation(tmp_path, observation())
    record_policy(evidence_db, policy(**changes), NOW)
    assert "offer_states" not in report(tmp_path)["candidates"][0]


def test_expired_or_future_capture_never_reaches_discovery(evidence_db, tmp_path):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    import_observation(tmp_path, observation(1))
    assert "offer_states" not in report(tmp_path)["candidates"][0]
    assert "offer_states" in report(tmp_path, NOW + timedelta(days=1))["candidates"][0]
    assert "offer_states" not in report(tmp_path, EXPIRY)["candidates"][0]


def test_unreviewed_source_work_is_not_attached(evidence_db, tmp_path):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    import_observation(tmp_path, replace(observation(), work_reviewed=False))
    assert "offer_states" not in report(tmp_path)["candidates"][0]
