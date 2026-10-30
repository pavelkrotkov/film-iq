"""Explicit local cache rights and expiry; no provider permission is inferred."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CachePolicy:
    source: str
    allowed: bool
    rights_evidence: str
    attribution: str
    expires_at: datetime
    terminated: bool = False
    version: str = "cache-policy-v1"

    def __post_init__(self) -> None:
        if not all(
            value.strip() for value in (self.source, self.rights_evidence, self.attribution)
        ):
            raise ValueError("source, rights evidence and attribution are required")
        if self.expires_at.utcoffset() is None:
            raise ValueError("expiry must be timezone-aware")


def status(policy: CachePolicy, now: datetime) -> str:
    if now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if policy.terminated or now >= policy.expires_at:
        return "purge_due"
    return "retain" if policy.allowed else "blocked"
