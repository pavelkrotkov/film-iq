from film_iq import __version__
from film_iq.cli import main


def test_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_status_does_not_claim_gate_a_verified(capsys) -> None:
    assert main(["status"]) == 0
    captured = capsys.readouterr().out
    assert "Gate A remains unverified" in captured
