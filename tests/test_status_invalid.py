"""Malformed configured state cannot claim current operation or reveal payloads."""

import json

import pytest

from film_iq.cli import main


@pytest.mark.parametrize(
    "value",
    [
        "private-secret",
        {
            "version": "private-run-v1",
            "stale": False,
            "attempted_at": "2026-10-30T00:00:00Z",
            "last_successful_run": None,
        },
    ],
)
def test_invalid_run_is_redacted(tmp_path, capsys, value):
    path = tmp_path / "run.json"
    path.write_text(json.dumps(value))
    assert main(["status", "--run-status", str(path), "--format", "json"]) == 1
    output = capsys.readouterr().out
    assert json.loads(output)["operations"]["state"] == "invalid"
    assert "private-secret" not in output and str(path) not in output


def test_unsupplied_paths_are_not_healthy(capsys):
    assert main(["status", "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert all(item["state"] == "not_configured" for item in result.values())
