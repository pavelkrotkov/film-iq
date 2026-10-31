"""Failures preserve the prior cursor and interrupted acquisitions remain visible."""

import json

import pytest
from test_curated_attempt import files

from film_iq.ingest import curated_attempt
from film_iq.ingest.acquisition import acquisition_status
from film_iq.ingest.curated_command import import_list_command
from film_iq.storage import connect


def test_failed_or_interrupted_import_can_retry_without_duplicate_evidence(tmp_path, monkeypatch):
    failure = RuntimeError
    source, manifest, database = files(tmp_path)
    first = json.loads(import_list_command(source, manifest, database))
    original = curated_attempt.import_list

    def crash(*args, **kwargs):
        original(*args, **kwargs)
        raise failure("synthetic failure")

    monkeypatch.setattr(curated_attempt, "import_list", crash)
    with pytest.raises(failure):
        import_list_command(source, manifest, database)
    with connect(database) as db:
        state = acquisition_status(db)[0]
        assert state["cursor"] == first["revision_id"]
        assert state["outcome"] == "error"
        assert "synthetic failure" not in json.dumps(state)
    monkeypatch.setattr(curated_attempt, "import_list", original)
    assert (
        json.loads(import_list_command(source, manifest, database))["revision_id"]
        == first["revision_id"]
    )
    with connect(database) as db:
        assert acquisition_status(db)[0]["outcome"] == "success"
        assert db.execute("SELECT count(*) FROM extraction_revision").fetchone() == (1,)


def test_manifest_does_not_override_existing_permission(tmp_path):
    column, value = "decision", "blocked"
    source, manifest, database = files(tmp_path)
    import_list_command(source, manifest, database)
    with connect(database) as db:
        db.execute(f"UPDATE acquisition_permission SET {column}=?", (value,))
    with pytest.raises(PermissionError):
        import_list_command(source, manifest, database)
    with connect(database) as db:
        assert db.execute("SELECT count(*) FROM acquisition_attempt").fetchone() == (1,)
