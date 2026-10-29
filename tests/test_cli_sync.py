import pytest

from film_iq.cli import main


def test_sync_defaults_to_preview_without_configuration(monkeypatch, capsys):
    monkeypatch.delenv("MOVARY_URL", raising=False)
    assert main(["sync", "--title", "Fixture film", "--tmdb-id", "1"]) == 0
    assert "Preview: add Fixture film (TMDB 1)" in capsys.readouterr().out


def test_sync_execution_requires_explicit_approval(capsys):
    with pytest.raises(SystemExit) as error:
        main(["sync", "--title", "Fixture film", "--tmdb-id", "1", "--execute"])
    assert error.value.code == 2
    assert "explicit approval" in capsys.readouterr().err
