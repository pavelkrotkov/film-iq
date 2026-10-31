"""Fresh private snapshots replace stale planner watched inputs."""

import json

import pytest
from discovery_fixtures import fresh_status, snapshot
from test_report import inputs
from test_report_runtime import setup_db

from film_iq.cli import main


def test_cli_personal_snapshot_overrules_stale_caller_watch_flag(evidence_db, tmp_path, capsys):
    setup_db(evidence_db)
    data = inputs()
    data["catalog"]["42"]["watched"] = True
    personal = snapshot()
    personal["films"][0]["tmdb_id"] = 1
    personal["films"][0]["personal_artistic_merit"] = 9
    personal["films"][0]["merit_status"] = "known"
    source = tmp_path / "personal.json"
    source.write_text(json.dumps(personal))
    source.with_suffix(".json.status").write_text(json.dumps(fresh_status()))
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(data))
    assert (
        main(
            [
                "report",
                "--database",
                str(tmp_path / "evidence.db"),
                "--inputs",
                str(path),
                "--snapshot",
                str(source),
                "--format",
                "json",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    film = result["plans"][0]["choices"][0]["film"]
    assert not film["watched"]
    assert (film["personal_enjoyment"], film["personal_artistic_merit"]) == (7, 9)
    assert "provenance" not in result["films"][0]
    source.with_suffix(".json.status").write_text('{"stale": true}')
    with pytest.raises(SystemExit):
        main(
            [
                "report",
                "--database",
                str(tmp_path / "evidence.db"),
                "--inputs",
                str(path),
                "--snapshot",
                str(source),
            ]
        )
