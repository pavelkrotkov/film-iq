"""CLI reimports log attempts while semantic revisions remain idempotent."""

import json
from dataclasses import asdict

from test_curated_csv import MANIFEST, body

from film_iq.ingest.acquisition import acquisition_status
from film_iq.ingest.curated_command import import_list_command
from film_iq.storage import connect


def files(tmp_path):
    source, manifest = tmp_path / "list.csv", tmp_path / "manifest.json"
    source.write_text(body())
    manifest.write_text(json.dumps(asdict(MANIFEST)))
    return source, manifest, tmp_path / "evidence.db"


def test_cli_reimport_has_two_attempts_but_one_revision(tmp_path):
    source, manifest, database = files(tmp_path)
    first = json.loads(import_list_command(source, manifest, database))
    second = json.loads(import_list_command(source, manifest, database))
    assert first["revision_id"] == second["revision_id"]
    with connect(database) as db:
        state = acquisition_status(db)[0]
        assert (state["outcome"], state["cursor"]) == ("success", first["revision_id"])
        assert db.execute("SELECT count(*) FROM acquisition_attempt").fetchone() == (2,)
        assert db.execute("SELECT count(*) FROM extraction_revision").fetchone() == (1,)
        assert db.execute("SELECT count(*) FROM entry_observation").fetchone() == (3,)
