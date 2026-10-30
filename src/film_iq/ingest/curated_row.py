"""A source row retains publication and identity assertions without guessing."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CuratedRow:
    source_id: str
    source_url: str
    edition: str
    ballot_scope: str
    position: int
    rank: int | None
    tie: str | None
    published_at: str | None
    eligibility_date: str | None
    raw_title: str
    director: str | None
    year: int | None
    tmdb_id: int | None
    identity_reviewer: str | None
    identity_evidence: str | None
    locator: str
