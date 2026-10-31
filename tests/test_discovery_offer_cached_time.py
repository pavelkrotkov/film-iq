"""A newer wrapper cannot visually refresh cached source observations."""

from dataclasses import replace
from datetime import timedelta

import pytest
from discovery_offer_support import configure, import_observation, observation, report
from offer_store_support import NOW, prepare


@pytest.mark.parametrize("mixed", [False, True])
def test_reimported_cached_claims_keep_original_visible_check_times(evidence_db, tmp_path, mixed):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    original = observation()
    import_observation(tmp_path, original)
    cached = original.assertions[0]
    later = NOW + timedelta(days=2)
    assertions = (
        (cached, replace(cached, checked_at=later, url="https://example.test/new"))
        if mixed
        else (cached,)
    )
    import_observation(tmp_path, replace(original, checked_at=later, assertions=assertions))
    main = report(tmp_path, later, "markdown").split("<details>", 1)[0]
    # Wrapper bookkeeping and each source observation have visibly different labels.
    assert "attempt recorded 2026-01-03 00:00 UTC" in main
    assert "(https://example.test/film) (claim checked 2026-01-01 00:00 UTC)" in main
    assert ("(https://example.test/new) (claim checked 2026-01-03 00:00 UTC)" in main) == mixed
    claims = report(tmp_path, later)["candidates"][0]["offer_states"][0]["current"]["assertions"]
    assert claims[0]["checked_at"] == NOW.isoformat()
