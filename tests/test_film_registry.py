from pathlib import Path

import pytest

from film_iq.ingest.adapters.film_registry import extract

FIXTURES = Path(__file__).parent / "fixtures/ingest/registry"


@pytest.mark.parametrize(
    ("year", "first", "last"),
    [
        (2020, "Suspense", "Freedom Riders"),
        (2022, "Mardi Gras Carnival", "Pariah"),
        (2025, "The Tramp and the Dog", "The Grand Budapest Hotel"),
    ],
)
def test_registry_selection(year: int, first: str, last: str) -> None:
    data = (FIXTURES / f"{year}.txt").read_bytes()
    result = extract(year, data)
    assert result == extract(year, data)
    assert len(result.entries) == 25
    assert result.entries[0].title == first
    assert result.entries[-1].title == last
    assert [entry.position for entry in result.entries] == list(range(1, 26))
    assert all(entry.rank is None for entry in result.entries)
    assert result.entries[0].locator == "transcription line 1"


@pytest.mark.parametrize("year", [2020, 2022, 2025])
def test_registry_provenance_and_invalid_transcriptions(year: int) -> None:
    data = (FIXTURES / f"{year}.txt").read_bytes()
    result = extract(year, data)
    assert "unknown" in result.ballot_completeness
    assert "primary" in result.lineage
    with pytest.raises(ValueError, match="review required"):
        extract(year, data.rsplit(b"\n", 2)[0] + b"\n")
    with pytest.raises(ValueError, match="review required"):
        extract(year, data.replace(b"(", b"[", 1))


def test_unknown_edition_requires_review() -> None:
    with pytest.raises(ValueError, match="review required"):
        extract(2000, b"")
