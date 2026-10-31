"""CLI and scheduled jobs forward display options without passing them to refresh."""

from unittest.mock import Mock

from operations_support import configuration

from film_iq import discovery_cli, operations_run


def test_discovery_cli_public_default_and_source_override(tmp_path, monkeypatch):
    command = Mock(return_value="{}")
    monkeypatch.setattr(discovery_cli, "discovery_command", command)
    path = tmp_path / "source.json"
    assert discovery_cli.main(["discover", "--cohort", str(path)]) == 0
    assert command.call_args.kwargs["order"] == "public-support"
    discovery_cli.main(["discover", "--cohort", str(path), "--order", "source"])
    assert command.call_args.kwargs["order"] == "source"


def test_scheduled_options_do_not_leak_into_personal_exports(tmp_path, monkeypatch):
    refresh, paths = configuration(tmp_path, monkeypatch)
    catalog = tmp_path / "catalog.json"
    command = Mock(return_value="Private shortlist")
    monkeypatch.setattr(operations_run, "discovery_command", command)
    operations_run.run_once(
        Mock(),
        **paths,
        catalog=catalog,
        order="public-support",
        ratings_csv=tmp_path / "ratings.csv",
    )
    assert refresh.call_args.kwargs == {"ratings_csv": tmp_path / "ratings.csv"}
    assert command.call_args.kwargs == {
        "catalog": catalog,
        "order": "public-support",
    }
