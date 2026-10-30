"""A second failed export cannot publish a mixed-generation snapshot."""

import subprocess
from unittest.mock import Mock

import pytest

from film_iq.personal_refresh import refresh

RATINGS = "title,year,tmdbId,imdbId,userRating\n"


def test_export_commands_staged_and_failed_second_export_never_replaces(tmp_path, monkeypatch):
    client, snapshot = Mock(), tmp_path / "snapshot.json"
    client.read.return_value = []
    snapshot.write_text("previous private snapshot")

    def run(command, *, stdout, **kwargs):
        if command == ["history"]:
            raise subprocess.CalledProcessError(1, command)
        stdout.write(RATINGS.encode())

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(ValueError):
        refresh(client, snapshot, ratings_command=["ratings"], history_command=["history"])
    assert snapshot.read_text() == "previous private snapshot"
    assert not list(tmp_path.glob(".refresh-*"))
