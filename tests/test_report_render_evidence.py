"""Render original and derivative evidence without counting the same vote twice."""

from dataclasses import asdict, replace
from datetime import date

import pytest

from film_iq.report_render import markdown
from film_iq.scoring import Evidence, score


@pytest.mark.parametrize(
    "context",
    [
        "[Aggregator](https://example.test/aggregate)",
        "rank unknown, partial",
        "published 2026-01-15; eligibility 2025 releases",
        "independence group critic-group",
        "lineage derivative: Quotes original ballot; derivative of ballot",
    ],
)
def test_markdown_preserves_excluded_derivative_context(context):
    original = Evidence(
        "42",
        "ballot",
        "https://example.test/ballot",
        date(2025, 12, 1),
        "critic-group",
        "2025 releases",
        2,
        author="Original critic",
        lineage_kind="original",
        lineage="original ballot",
        completeness="complete",
    )
    derivative = replace(
        original,
        list_id="aggregate",
        url="https://example.test/aggregate",
        published=date(2026, 1, 15),
        author="Aggregator",
        rank=None,
        lineage_kind="derivative",
        lineage="Quotes original ballot",
        derivative_of=("ballot",),
        completeness="partial",
    )
    report = {
        "assumptions": "Fixture",
        "crosswalk": {"42": 1},
        "evidence": [asdict(result) for result in score([original, derivative])],
        "plans": [],
        "offers": [],
        "previews": {},
    }
    rendered = markdown(report)
    assert "1 independent endorsements" in rendered
    assert "Contributing: [Original critic](https://example.test/ballot)" in rendered
    excluded = next(line for line in rendered.splitlines() if "Excluded" in line)
    assert context in excluded
