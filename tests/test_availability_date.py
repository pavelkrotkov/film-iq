"""Dated jobs cannot consume quota on an unintended UTC date."""

import sys
from datetime import UTC, datetime, timedelta

import pytest

from docs.research.availability import run


def test_wrong_utc_date_makes_no_observation(monkeypatch, tmp_path, capsys):
    tomorrow = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()
    output = tmp_path / ".cache" / "future.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "availability.run",
            "--provider",
            "both",
            "--output",
            str(output),
            "--live",
            "--on-date",
            tomorrow,
        ],
    )

    def unexpected_observation(*args):
        pytest.fail("a wrong-date run must not observe the cohort")

    monkeypatch.setattr(run, "observe_cohort", unexpected_observation)
    with pytest.raises(SystemExit) as error:
        run.main()
    assert error.value.code == 2
    assert "--on-date must match today in UTC" in capsys.readouterr().err
    assert not output.exists()
