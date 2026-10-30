"""A known accepted curated publication day survives unknown normalized metadata."""

from dataclasses import replace

import pytest
from test_accept import AUDIT
from test_curated_csv import MANIFEST, body

from film_iq.discovery import build_discovery
from film_iq.discovery_render import markdown
from film_iq.ingest.accept import accept
from film_iq.ingest.curated import import_list


def test_dated_curated_import_reaches_report_without_losing_publication_day(evidence_db):
    selected = import_list(
        body(published_at="2025-12-20"),
        MANIFEST,
        db=evidence_db,
        accessed_at="2026-10-30T00:00:00+00:00",
    )
    accept(
        evidence_db,
        selected["revision_id"],
        replace(AUDIT, expected_count=3),
        previous_revision_id=None,
    )
    report = build_discovery(selected, db=evidence_db)
    assert [item["published_at"] for item in report["candidates"]] == ["2025-12-20"] * 3
    assert "published 2025-12-20" in markdown(report)
    truncated = {**selected, "candidates": selected["candidates"][:-1], "total_candidates": 2}
    with pytest.raises(ValueError, match="complete current accepted revision"):
        build_discovery(truncated, db=evidence_db)
