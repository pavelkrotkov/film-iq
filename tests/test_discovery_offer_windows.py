"""Known source bounds must qualify visible links, not hide only in JSON."""

from dataclasses import replace
from datetime import datetime, timedelta

import pytest
from discovery_offer_support import configure, import_observation, observation, report
from offer_store_support import NOW, prepare


@pytest.mark.parametrize(
    "field,value,label",
    [
        ("asserted_expires_at", "2026-01-01T12:00:00+00:00", "source says expires"),
        ("asserted_added_on", "2026-01-03T00:00:00+00:00", "source says starts"),
    ],
)
def test_ended_or_future_source_window_is_visible_before_audit(
    evidence_db, tmp_path, field, value, label
):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    source = observation()
    assertion = replace(source.assertions[0], **{field: datetime.fromisoformat(value)})
    import_observation(tmp_path, replace(source, assertions=(assertion,)))
    output = report(tmp_path, NOW + timedelta(days=1), "markdown")
    main = output.split("<details>", 1)[0]
    assert f"{label} {value}" in main
    assert "Reported options; verify with the service" in main
    result = report(tmp_path, NOW + timedelta(days=1))
    assert result["candidates"][0]["offer_states"][0]["current"]["assertions"][0][field] == value
