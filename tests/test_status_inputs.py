"""Status exposes successful times and stale generations, never personal contents."""

import json

from film_iq.cli import main
from film_iq.personal_snapshot import VERSION


def test_personal_generation_mismatch_is_stale_and_private(tmp_path, capsys):
    path = tmp_path / "snapshot.json"
    snapshot = {
        "version": VERSION,
        "last_successful_refresh": "2026-10-30T00:00:00Z",
        "films": [],
        "provenance": {"private": "secret"},
    }
    path.write_text(json.dumps(snapshot))
    path.with_suffix(".json.status").write_text(
        json.dumps({"stale": False, "last_successful_refresh": "other"})
    )
    before = path.read_bytes()
    assert (
        main(
            ["status", "--snapshot", str(path), "--now", "2026-10-31T00:00:00Z", "--format", "json"]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert json.loads(output)["personal"]["state"] == "stale"
    assert "secret" not in output and str(path) not in output
    assert path.read_bytes() == before


def test_successful_run_and_missing_input_are_explicit(tmp_path, capsys):
    path = tmp_path / "run.json"
    path.write_text(
        json.dumps(
            {
                "version": "private-run-v1",
                "attempted_at": "2026-10-30T00:00:00Z",
                "last_successful_run": "2026-10-30T00:01:00Z",
                "stale": False,
                "error": "private-secret",
            }
        )
    )
    assert (
        main(
            [
                "status",
                "--run-status",
                str(path),
                "--database",
                str(tmp_path / "missing.db"),
                "--format",
                "json",
            ]
        )
        == 1
    )
    output = capsys.readouterr().out
    result = json.loads(output)
    assert result["operations"]["state"] == "current"
    assert result["acquisition"]["state"] == "missing"
    assert not (tmp_path / "missing.db").exists() and "private-secret" not in output
