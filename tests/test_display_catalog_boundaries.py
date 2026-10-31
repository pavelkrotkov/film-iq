"""Reject duplicate identities and overlong or timezone-unknown display metadata."""

from datetime import timedelta

import pytest
from display_fixtures import NOW, catalog_path, payload

from film_iq.display_catalog import read_catalog


def test_duplicate_work_ids_are_not_silently_overwritten(tmp_path):
    data = payload()
    data["records"] *= 2
    with pytest.raises(ValueError, match="unique"):
        read_catalog(catalog_path(tmp_path, data), NOW)


def test_expiry_cannot_exceed_180_days_or_omit_timezone(tmp_path):
    data = payload()
    data["expires_at"] = (NOW + timedelta(days=181)).isoformat()
    with pytest.raises(ValueError, match="180days"):
        read_catalog(catalog_path(tmp_path, data), NOW)
    data["expires_at"] = "2026-11-01T00:00:00"
    with pytest.raises(ValueError, match="timezone"):
        read_catalog(catalog_path(tmp_path, data), NOW)
