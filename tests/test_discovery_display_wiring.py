"""CLI and scheduled jobs forward display options without passing them to refresh."""

from unittest.mock import Mock

from film_iq import discovery_cli


def test_discovery_cli_public_default_and_source_override(tmp_path, monkeypatch):
    command = Mock(return_value="{}")
    monkeypatch.setattr(discovery_cli, "discovery_command", command)
    path = tmp_path / "source.json"
    catalog = tmp_path / "catalog.json"
    assert discovery_cli.main(["discover", "--cohort", str(path), "--catalog", str(catalog)]) == 0
    assert command.call_args.kwargs == {"catalog": catalog, "order": "public-support"}
    discovery_cli.main(["discover", "--cohort", str(path), "--order", "source"])
    assert command.call_args.kwargs["order"] == "source"
