"""Reviewed display metadata needs bounded freshness and explicit factual provenance."""

from datetime import timedelta

import pytest
from display_fixtures import NOW, catalog_path, payload

from film_iq.display_catalog import read_catalog


def test_fresh_reviewed_facts_are_allowlisted_and_attributed(tmp_path):
    data = payload()
    data["records"][0]["overview"] = "Synthetic unneeded prose"
    records, context = read_catalog(catalog_path(tmp_path, data), NOW)
    assert records[123]["runtime_minutes"] == 105
    assert "overview" not in records[123]
    assert (context["status"], context["attribution"]) == ("fresh", "Synthetic reviewed metadata")


def test_expired_or_future_snapshot_provides_no_display_facts(tmp_path):
    path = catalog_path(tmp_path)
    assert read_catalog(path, NOW + timedelta(days=6))[0] == {}
    assert read_catalog(path, NOW - timedelta(days=2))[1]["status"] == "not_yet_valid"
    assert read_catalog(None, NOW) == ({}, {"status": "not_supplied"})


@pytest.mark.parametrize(
    "field,value", [("reviewer", " "), ("runtime_minutes", 0), ("tmdb_id", True)]
)
def test_invalid_review_claims_are_rejected(tmp_path, field, value):
    data = payload()
    data["records"][0][field] = value
    with pytest.raises(ValueError):
        read_catalog(catalog_path(tmp_path, data), NOW)
