"""Audit assertions supplied by a human reviewer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditAttestation:
    """Assertions made by the auditor; independence is not system-verified."""

    auditor: str
    evidence: str
    audited_at: str
    independent: bool
    complete: bool
    expected_count: int


def validate_audit(audit: AuditAttestation) -> None:
    """Require an explicit complete, independent attestation with evidence."""
    if not all(value.strip() for value in (audit.auditor, audit.evidence, audit.audited_at)):
        raise ValueError("auditor, evidence and audit time are required")
    if audit.independent is not True or audit.complete is not True or audit.expected_count < 1:
        raise ValueError("independent and complete audit with positive count required")
