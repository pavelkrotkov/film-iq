"""Malformed variants remain partial, preserving valid positive rows and date units."""

from datetime import UTC, datetime

import pytest
from candidate_support import WORK, native_payload, native_row
from offer_store_support import NOW

from film_iq.availability.candidate_native import normalize


@pytest.mark.parametrize(
    "changes",
    [
        {"price": {"amount": 1.99, "currency": "USD"}},
        {"availableSince": True},
        {"expiresOn": 1.2},
        {"type": "unsupported"},
        {"link": "https://example.test/?api_key=fixture-secret"},
    ],
)
def test_invalid_variant_never_silently_completes_or_removes(changes):
    result = normalize(WORK, native_payload([native_row(), native_row(**changes)]), NOW)
    assert result.status == "partial"
    assert len(result.assertions) == 1


def test_native_detection_is_not_effective_start_and_last_day_not_expiry_instant():
    item = normalize(WORK, native_payload(), NOW).assertions[0]
    assert item.provider_detected_at == datetime(2025, 12, 31, 23, tzinfo=UTC)
    assert item.provider_last_day_at == datetime(2026, 1, 3, tzinfo=UTC)
    assert (item.asserted_added_on, item.asserted_expires_at, item.opportunity.plan) == (
        None,
        None,
        None,
    )
