"""Failed delivery must leave acknowledgement unchanged."""

from unittest.mock import patch

import pytest
from test_changes_command import arguments

from film_iq.cli import main


def test_broken_stdout_does_not_acknowledge(evidence_db, tmp_path):
    with (
        patch("builtins.print", side_effect=BrokenPipeError("closed pipe")),
        pytest.raises(SystemExit),
    ):
        main([*arguments(tmp_path), "--ack"])
    assert not (tmp_path / "seen.json").exists()


def test_failed_private_output_does_not_acknowledge(evidence_db, tmp_path):
    output = tmp_path / "directory"
    output.mkdir()
    with pytest.raises(SystemExit):
        main([*arguments(tmp_path), "--output", str(output), "--ack"])
    assert not (tmp_path / "seen.json").exists()


def test_markdown_private_output_and_invalid_checkpoint(evidence_db, tmp_path):
    args = arguments(tmp_path)
    args[-1] = "markdown"
    output = tmp_path / "changes.md"
    assert main([*args, "--output", str(output), "--ack"]) == 0
    assert "First-use baseline" in output.read_text()
    assert output.stat().st_mode & 0o777 == 0o600
    (tmp_path / "seen.json").write_text('{"provider_payload":"forbidden"}')
    with pytest.raises(SystemExit):
        main(args)


def test_output_cannot_overwrite_checkpoint_or_database(evidence_db, tmp_path):
    for name in ("evidence.db", "seen.json"):
        with pytest.raises(SystemExit):
            main([*arguments(tmp_path), "--output", str(tmp_path / name)])
