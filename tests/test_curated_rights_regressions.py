"""Malformed JSON must not bypass source-rights validation or open storage."""

import json
from dataclasses import asdict

import pytest
from test_curated_csv import MANIFEST, body

from film_iq.ingest.curated_command import import_list_command


def test_malformed_rights_reject_before_database_open(tmp_path):
    field, value = "rights_evidence", None
    manifest = asdict(MANIFEST)
    manifest[field] = value
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    source = tmp_path / "selection.csv"
    source.write_text(body())
    database = tmp_path / "must-not-exist.db"
    with pytest.raises(ValueError, match="rights metadata"):
        import_list_command(source, path, database)
    assert not database.exists()
