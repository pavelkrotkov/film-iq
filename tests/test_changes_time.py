"""An earlier assessment cannot consume later observations or acceptances."""

from dataclasses import replace
from datetime import datetime, timedelta

import pytest
from offer_store_support import NOW, fetch, prepare
from test_accept import AUDIT, pending
from test_acquisition import permit

from film_iq.availability.ledger import save_fetch
from film_iq.availability.state import read_state
from film_iq.changes import digest
from film_iq.ingest.accept import accept


def test_future_offer_is_not_emitted_or_consumed_even_by_first_baseline(evidence_db):
    prepare(evidence_db)
    save_fetch(evidence_db, fetch(), NOW)
    _, baseline = digest(evidence_db, None, NOW)
    future = NOW + timedelta(days=2)
    save_fetch(evidence_db, fetch(2, present=False), future)
    # Even a first-use baseline must leave a later event unseen.
    before, unchanged = digest(evidence_db, baseline, future - timedelta(seconds=1))
    _, initial = digest(evidence_db, None, future - timedelta(seconds=1))
    assert unchanged == initial == baseline
    assert before["offer_changes"] == []
    assert len(read_state(evidence_db, fetch(), future - timedelta(seconds=1))["events"]) == 1
    boundary, acknowledged = digest(evidence_db, unchanged, future)
    assert [e["change"]["kind"] for e in boundary["offer_changes"]] == ["source_absent"]
    assert (
        digest(evidence_db, acknowledged, future + timedelta(seconds=1))[0]["offer_changes"] == []
    )


@pytest.mark.parametrize("field", ["capture", "audit"])
def test_source_capture_and_acceptance_boundaries_respect_offsets(evidence_db, field):
    db = evidence_db
    pending(db)
    permit(db, reviewed_at="2026-01-01T00:00:00+00:00")
    start = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    _, baseline = digest(db, None, start)
    audit = replace(
        AUDIT, audited_at="2026-01-03T01:00:00+02:00" if field == "audit" else "unknown"
    )
    accept(db, "new", audit, previous_revision_id="rev")
    if field == "capture":
        db.execute("UPDATE source_document SET accessed_at='2026-01-03T01:00:00+02:00'")
    # The source date differs from UTC at the exact eligibility boundary.
    boundary = datetime.fromisoformat("2026-01-02T23:00:00+00:00")
    early, unchanged = digest(db, baseline, boundary - timedelta(seconds=1))
    _, initial = digest(db, None, boundary - timedelta(seconds=1))
    assert early["source_changes"] == [] and unchanged == baseline
    assert initial["source_revisions"] == {}
    result, acknowledged = digest(db, unchanged, boundary)
    assert result["source_changes"][0]["revision_id"] == "new"
    assert digest(db, acknowledged, boundary + timedelta(seconds=1))[0]["source_changes"] == []
