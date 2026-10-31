"""Compare wikitext adapters with a separate agent's rendered-HTML oracle."""

import json
from pathlib import Path

import pytest

from film_iq.ingest.adapters import nbr_pages, sight_sound_pages

PAGES = Path(__file__).parent / "fixtures/ingest/pages"
AUDIT = json.loads((PAGES.parents[3] / "docs/a6/independent-fixture-audit.json").read_text())
CASES = {
    "nbr-2022": (nbr_pages.extract, 2022),
    "nbr-2023": (nbr_pages.extract, 2023),
    "sight-sound-2012": (sight_sound_pages.extract, 2012),
    "sight-sound-2022": (sight_sound_pages.extract, 2022),
}


def captured(key):
    adapter, year = CASES[key]
    return adapter(year, (PAGES / f"{key}.json").read_bytes())


@pytest.mark.parametrize(
    ("expected",),
    [
        (AUDIT["per_page"][1],),
        (AUDIT["per_page"][3],),
    ],
)
def test_complete_records_match_independent_rendered_oracle(expected):
    result = captured(expected["key"])
    records = [
        {"title": entry.title, "position": entry.position, "rank": entry.rank, "tie": entry.tie}
        for entry in result.entries
    ]
    assert records == expected["expected_entries"]
    assert result.document_revision == str(expected["revision"])
    assert result == captured(expected["key"])
