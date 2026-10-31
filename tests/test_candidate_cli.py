"""The real CLI can use an injected fixture transport and existing reviewed policy."""

from candidate_support import manifest, native_payload, permit, response
from discovery_offer_support import configure, report
from offer_store_support import NOW

from film_iq.availability import candidate_command
from film_iq.availability.candidate_run import run_candidates


def test_cli_to_ledger_to_discovery_has_no_live_dependency(
    evidence_db, tmp_path, monkeypatch, capsys
):
    configure(evidence_db, tmp_path)
    permit(evidence_db)
    monkeypatch.setenv("MOVIE_OF_THE_NIGHT_API_KEY", "fixture-secret")
    get = response(native_payload())
    monkeypatch.setattr(
        candidate_command,
        "run_candidates",
        lambda db, provider, works, **options: run_candidates(
            db, provider, works, now=NOW, get=get, **options
        ),
    )
    path = manifest(tmp_path / "works.json")
    assert (
        candidate_command.main(
            [
                "--provider",
                "motn",
                "--input",
                str(path),
                "--database",
                str(tmp_path / "evidence.db"),
                "--max-requests",
                "1",
                "--live",
            ]
        )
        == 0
    )
    assert get.call_count == 1
    assert "fixture-secret" not in capsys.readouterr().out
    assert (
        report(tmp_path)["candidates"][0]["offer_states"][0]["latest_attempt"]["source"] == "motn"
    )
