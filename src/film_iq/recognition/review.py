"""Explicit independent classification and source-use review assertions."""

from dataclasses import dataclass
from datetime import datetime

from film_iq.recognition.checks import names


@dataclass(frozen=True)
class ClassificationReview:
    auditor: str
    evidence: str
    reviewed_at: str
    independent: bool
    rights_allowed: bool
    rights_evidence: str
    permitted_use: str

    def __post_init__(self) -> None:
        names(self.auditor, self.evidence, self.rights_evidence, self.permitted_use)
        if self.independent is not True or self.rights_allowed is not True:
            raise ValueError("explicit independent classification and allowed source use required")
        if datetime.fromisoformat(self.reviewed_at).utcoffset() is None:
            raise ValueError("classification review time must be timezone-aware")
