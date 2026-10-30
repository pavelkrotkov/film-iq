"""First-use commands share the film-iq entry point without live I/O."""

import json

import pytest
from discovery_fixtures import cohort

from film_iq.cli import main


def test_discover_cli_shows_pending_without_creating_database(tmp_path, capsys):
    path = tmp_path / "cohort.json"
    path.write_text(json.dumps(cohort()))
    assert main(["discover", "--cohort", str(path), "--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert (report["accepted"], report["suggested_unwatched"]) == (0, [])
    assert sorted(p.name for p in tmp_path.iterdir()) == ["cohort.json"]


def test_import_list_cli_reuses_curated_validation(tmp_path, capsys):
    from dataclasses import asdict

    from test_curated_csv import MANIFEST, body

    source, manifest = tmp_path / "source.csv", tmp_path / "manifest.json"
    source.write_text(body())
    manifest.write_text(json.dumps(asdict(MANIFEST)))
    assert main(["import-list", "--csv", str(source), "--manifest", str(manifest)]) == 0
    assert json.loads(capsys.readouterr().out)["total_candidates"] == 3


def test_acquisition_status_does_not_create_missing_database(tmp_path):
    with pytest.raises(SystemExit):
        main(["acquisition-status", "--database", str(tmp_path / "missing.db")])
    assert not (tmp_path / "missing.db").exists()
