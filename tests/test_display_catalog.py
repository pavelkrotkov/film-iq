"""Reviewed display metadata needs bounded freshness and explicit factual provenance."""

from display_fixtures import NOW, catalog_path, payload

from film_iq.display_catalog import read_catalog


def test_fresh_reviewed_facts_are_allowlisted_and_attributed(tmp_path):
    data = payload()
    data["records"][0]["overview"] = "Synthetic unneeded prose"
    records, context = read_catalog(catalog_path(tmp_path, data), NOW)
    assert records[123]["runtime_minutes"] == 105
    assert "overview" not in records[123]
    assert (context["status"], context["attribution"]) == ("fresh", "Synthetic reviewed metadata")
