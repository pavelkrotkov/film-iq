from pathlib import Path
from unittest import TestCase

from film_iq.ingest.adapters.nbr_2023 import extract

FIXTURE = Path(__file__).parent / "fixtures/ingest/nbr-2023.wiki"


def test_provisional_nbr_section() -> None:
    data = FIXTURE.read_bytes()
    result = extract(data)
    assert result == extract(data)
    assert [entry.title for entry in result.entries] == [
        "Killers of the Flower Moon",
        "Barbie",
        "The Boy and the Heron",
        "Ferrari",
        "The Holdovers",
        "The Iron Claw",
        "Maestro",
        "Oppenheimer",
        "Past Lives",
        "Poor Things",
    ]
    assert [entry.rank for entry in result.entries] == [1] + [None] * 9
    assert result.document_revision == "1370562803"
    assert result.review_status == "provisional; review required"
    assert "association" in result.review_reason
    assert result.ballot_completeness == "unknown"
    assert "other page sections excluded" in result.extraction_scope
    assert "derivative" in result.lineage
    assert result.entries[1].raw_context == "* ''[[Barbie (film)|Barbie]]''"
    assert result.entries[1].locator == "line 5"
    with TestCase().assertRaisesRegex(ValueError, "review required"):
        extract(data.replace(b"* ''[[Poor Things (film)|Poor Things]]''\n", b""))
    with TestCase().assertRaisesRegex(ValueError, "review required"):
        extract(data.replace(b"Barbie", b"Different"))
