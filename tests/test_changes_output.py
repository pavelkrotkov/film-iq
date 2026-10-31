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
