"""Explicit curated source policy and scope; permissions are caller attestations."""

from dataclasses import asdict, dataclass

from film_iq.ingest.curated_validate import _required_strings
from film_iq.ingest.persist_checks import SourcePolicy
from film_iq.recognition.models import SELECTIONS


@dataclass(frozen=True)
class CuratedList:
    policy: SourcePolicy
    edition: str
    ballot_scope: str
    document_revision: str
    eligibility: str
    completeness: str
    scope: str
    lineage: str
    rank_semantics: str
    rights_status: str
    rights_evidence: str
    permitted_use: str
    expected_count: int
    evidence_kind: str = "unknown"

    def __post_init__(self) -> None:
        strings = asdict(self)
        del strings["policy"], strings["expected_count"]
        _required_strings(strings)
        _required_strings(asdict(self.policy))
        if self.evidence_kind not in SELECTIONS:
            raise ValueError(
                "curated lists require a selection kind; awards/metrics use typed classification"
            )
        if self.rights_status != "allowed" or self.expected_count < 1:
            raise ValueError("documented allowed use and expected selection count required")
        if self.completeness not in {"complete", "intentionally_partial"}:
            raise ValueError("selection completeness must be declared")
