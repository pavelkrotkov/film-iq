"""Deterministic advice timing, with caller-declared freshness rather than a cadence."""

from datetime import datetime, timedelta

from .assertion import Assertion
from .validation import aware


def purchase_window(item: Assertion, now: datetime, max_age: timedelta) -> bool:
    aware(now)
    if max_age < timedelta():
        raise ValueError("maximum observation age must be nonnegative")
    if not item.checked_at <= now <= item.checked_at + max_age:
        return False
    return (item.asserted_added_on is None or item.asserted_added_on <= now) and (
        item.asserted_expires_at is None or now < item.asserted_expires_at
    )
