"""Every selected ballot must be complete and personal freshness gates the full report."""

import pytest
from discovery_fixtures import snapshot
from test_discovery_batch import selection

from film_iq.discovery_batch import build_discoveries


def test_duplicate_selection_and_truncated_second_ballot_fail(evidence_db):
    first, second = [selection(evidence_db, edition) for edition in ("2023-a", "2024-a")]
    with pytest.raises(ValueError, match="duplicate"):
        build_discoveries([first, first], db=evidence_db)
    second.update(candidates=[], total_candidates=0)
    with pytest.raises(ValueError, match="complete current accepted"):
        build_discoveries([first, second], db=evidence_db)


def test_stale_snapshot_suppresses_all_cohorts(evidence_db):
    cohorts = [selection(evidence_db, edition) for edition in ("2023-a", "2024-a")]
    report = build_discoveries(cohorts, snapshot(), db=evidence_db)
    assert report["personal_state_stale"] is True
    assert report["suggested_unwatched"] == []
