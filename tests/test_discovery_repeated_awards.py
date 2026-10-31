"""Single and multi-cohort paths share reviewed-work coalescing and flat reasons."""

import json

from discovery_fixtures import fresh_status, snapshot
from recognition_award_cohorts import award_cohort

from film_iq.discovery import build_discovery
from film_iq.discovery_batch import build_discoveries
from film_iq.discovery_render import markdown


def assert_work(report, count):
    assert (report["total_candidates"], report["accepted"], len(report["candidates"])) == (
        count,
        count,
        count,
    )
    assert len(report["suggested_unwatched"]) == 1
    work = report["suggested_unwatched"][0]
    assert len(work["source_reasons"]) == count
    assert all("source_reasons" not in reason for reason in work["source_reasons"])
    assert len(work["public_evidence_components"]["award_outcome"]) == count
    main = markdown(report).split("<details>", 1)[0]
    assert main.count("#### [Fixture repeated film") == 1
    json.dumps(report, default=str)  # No self-referencing aggregate/reason objects.
    return main, work


def test_repeated_award_categories_coalesce_in_single_and_multi_reports(evidence_db):
    first = award_cohort(evidence_db, "A")
    single = build_discovery(first, snapshot(), db=evidence_db, refresh_status=fresh_status())
    main, _ = assert_work(single, 3)
    assert all(f"Category A-{position}" in main for position in (1, 2, 5))
    second = award_cohort(evidence_db, "B")
    multi = build_discoveries(
        [first, second], snapshot(), db=evidence_db, refresh_status=fresh_status()
    )
    main, work = assert_work(multi, 6)
    assert [(reason["edition"], reason["position"]) for reason in work["source_reasons"]] == [
        (edition, position) for edition in ("A", "B") for position in (1, 2, 5)
    ]
    assert all(f"Category B-{position}" in main for position in (1, 2, 5))
