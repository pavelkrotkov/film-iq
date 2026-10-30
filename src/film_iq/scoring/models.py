"""Public evidence and separate, uncalibrated scoring outputs."""

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from typing import Literal


@dataclass(frozen=True)
class Evidence:
    film_id: str
    list_id: str
    url: str
    published: date | None
    independence_group: str
    eligibility: str
    rank: int | None = None
    derivative_of: tuple[str, ...] = ()
    entry_id: str | None = None
    revision_id: str | None = None
    match_decision_id: str | None = None
    source_id: str | None = None
    document_id: str | None = None
    locator: str | None = None
    lineage_kind: str | None = None
    lineage: str | None = None
    author: str | None = None
    completeness: str | None = None
    rank_semantics: str | None = None
    person_id: str | None = None
    source_family: str | None = None

    def __post_init__(self) -> None:
        if self.rank is not None and self.rank < 1:
            raise ValueError("rank must be positive or unknown")
        if self.person_id is not None and not self.person_id.strip():
            raise ValueError("person_id must be a reviewed nonblank ID or unknown")


@dataclass(frozen=True)
class Score:
    """Baseline evidence-group support, never an inferred critic headcount.

    Only explicit reviewed person_id values establish known people. Publisher
    or author strings alone never establish person identity across publications.

    Accepted extraction/match decisions are eligibility gates, not measurements
    of reliability. Neither endorsement counts nor ranks measure disagreement.
    Prediction uncertainty does not apply without a personal preference model.
    """

    film_id: str
    version: str
    independent_count: int
    rank_score: Fraction | None
    contributing: tuple[Evidence, ...]
    excluded: tuple[Evidence, ...]
    unranked_count: int
    partial_count: int
    extraction_uncertainty: Literal["not_evaluated"] = "not_evaluated"
    identity_uncertainty: Literal["not_evaluated"] = "not_evaluated"
    evidence_disagreement_uncertainty: Literal["not_evaluated"] = "not_evaluated"
    prediction_uncertainty: Literal["not_applicable"] = "not_applicable"
    known_person_count: int = 0
    unknown_contributor_count: int = 0
