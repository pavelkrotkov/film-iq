"""The scheduler CLI uses the same explicit display/order options as discovery."""

from unittest.mock import Mock

from film_iq import operations


def test_scheduler_cli_passes_catalog_and_public_default(tmp_path, monkeypatch):
    run = Mock(return_value={"last_successful_run": "synthetic"})
    monkeypatch.setattr(operations, "run_once", run)
    monkeypatch.setattr(operations, "MovaryClient", Mock())
    monkeypatch.setattr(operations, "_required_env", lambda name: "synthetic")
    args = []
    for name in (
        "database",
        "snapshot",
        "report",
        "backups",
        "status",
        "cohort",
        "ratings-csv",
        "history-csv",
        "catalog",
    ):
        args.extend([f"--{name}", str(tmp_path / name)])
    assert operations.main(args) == 0
    assert run.call_args.kwargs["catalog"] == tmp_path / "catalog"
    assert run.call_args.kwargs["order"] == "public-support"
