"""Synthetic facts only; no publisher content or personal ratings."""

import csv
import io
from dataclasses import replace

import pytest

from film_iq.ingest.curated import CuratedList, extraction, import_list
from film_iq.ingest.curated_csv import COLUMNS, read_csv
from film_iq.ingest.persist_checks import SourcePolicy

POLICY = SourcePolicy(
    "critic",
    "Synthetic critic",
    "https://example.test",
    "critic",
    "person-a",
    "manual allowed",
    "factual records",
    "synthetic",
    "example",
)
MANIFEST = CuratedList(
    POLICY,
    "2024-person-a",
    "person-a",
    "manual-1",
    "seen in 2024",
    "intentionally_partial",
    "first three published selections",
    "original",
    "ranked with ties",
    "allowed",
    "synthetic fixture",
    "local research",
    3,
)


def body(**changes):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=COLUMNS)
    writer.writeheader()
    for position, rank, tie in ((1, "1", "joint-1"), (2, "1", "joint-1"), (5, "", "")):
        row = dict.fromkeys(COLUMNS, "")
        row.update(
            source_id="critic",
            source_url="https://example.test/list",
            edition="2024-person-a",
            ballot_scope="person-a",
            position=str(position),
            rank=rank,
            tie=tie,
            raw_title=f"Synthetic film {position}",
            locator=f"row {position}",
        )
        row.update(changes)
        writer.writerow(row)
    return output.getvalue()


def test_ranks_unknowns_and_partial_selection():
    rows = read_csv(body())
    assert [(r.position, r.rank, r.tie) for r in rows] == [
        (1, 1, "joint-1"),
        (2, 1, "joint-1"),
        (5, None, None),
    ]
    assert rows[0].year is rows[0].published_at is rows[0].tmdb_id is None
    captured, _ = extraction(body(), MANIFEST)
    assert captured.ballot_completeness == "intentionally_partial"
    preview = import_list(body(), MANIFEST, accessed_at="2026-10-30T00:00:00Z")
    assert (
        preview["total_candidates"],
        preview["accepted"],
        preview["unresolved"],
        preview["watched_excluded"],
    ) == (3, 0, 3, 0)


@pytest.mark.parametrize(
    "change",
    [
        {"rank": "0"},
        {"position": ""},
        {"rank": "", "tie": "a"},
        {"tmdb_id": "123"},
        {"year": "unknown"},
        {"published_at": "2024"},
        {"raw_title": " "},
        {"source_url": "file:///private"},
    ],
)
def test_rejects_invalid_facts(change):
    with pytest.raises(ValueError):
        read_csv(body(**change))


def test_rejects_schema_and_incomplete_selection():
    with pytest.raises(ValueError, match="header"):
        read_csv(body().replace("raw_title", "other"))
    with pytest.raises(ValueError, match="count"):
        extraction(body(), replace(MANIFEST, expected_count=4))
    with pytest.raises(ValueError, match="allowed"):
        replace(MANIFEST, rights_status="unknown")
    with pytest.raises(ValueError, match="unique"):
        read_csv(body(position="1"))
