"""Explicit curated source policy and scope; permissions are caller attestations."""

from dataclasses import asdict, dataclass

from film_iq.ingest.persist_checks import SourcePolicy


def _required_strings(data: dict) -> None:
    strings = (value for value in data.values() if isinstance(value, str))
    if not all(value.strip() for value in strings):
        raise ValueError("explicit source, scope, lineage and rights metadata required")


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

    def __post_init__(self) -> None:
        _required_strings(asdict(self))
        _required_strings(asdict(self.policy))
        if self.rights_status != "allowed" or self.expected_count < 1:
            raise ValueError("documented allowed use and expected selection count required")
        if self.completeness not in {"complete", "intentionally_partial"}:
            raise ValueError("selection completeness must be declared")
