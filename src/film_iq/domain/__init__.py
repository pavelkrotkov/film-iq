"""Typed inputs shared by source adapters and persistence."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Observation:
    """One source entry in an extraction revision; rank is not display order."""

    source_id: str
    edition_id: str
    entry_id: str
    run_id: str
    revision_id: str
    raw_title: str
    raw_context: str
    locator: str
    rank: int | None = None
    tie: str | None = None
    original_title: str | None = None
    year: int | None = None
    director: str | None = None
    position: int | None = None
    extraction_decision: str = "pending"
    raw_imdb_id: str | None = None
    raw_tmdb_id: str | None = None

    # A position is display order; only a published rank is a rank.
    # The same entry may have observations from different revisions.
    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.source_id,
                self.edition_id,
                self.entry_id,
                self.run_id,
                self.revision_id,
                self.raw_title,
                self.locator,
            )
        ):
            raise ValueError("observation identifiers, raw title and locator must not be blank")
        if self.rank is not None and self.rank < 1:
            raise ValueError("rank must be positive")
