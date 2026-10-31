"""Explicit independent work review, never inferred from a provider's search hit."""

import re
from dataclasses import dataclass

from film_iq.availability.validation import positive_id, required


@dataclass(frozen=True)
class ReviewedWork:
    tmdb_id: int
    imdb_id: str
    reviewer: str
    evidence: str
    independent: bool

    def __post_init__(self) -> None:
        positive_id(self.tmdb_id)
        if not all(
            isinstance(value, str) for value in (self.imdb_id, self.reviewer, self.evidence)
        ):
            raise ValueError("review identity and provenance must be explicit strings")
        required(self.reviewer, self.evidence)
        if not re.fullmatch(r"tt[0-9]+", self.imdb_id) or self.independent is not True:
            raise ValueError("an independently reviewed TMDB/IMDb work crosswalk is required")
