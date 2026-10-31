"""Reject incomplete review or oversized input before even the first request."""

import json
from dataclasses import asdict, replace
from unittest.mock import Mock

import pytest
from candidate_support import WORK

from film_iq.availability import candidate_command
from film_iq.availability.candidate_run import run_candidates


def test_invalid_later_crosswalk_rejects_entire_cli_batch(tmp_path, monkeypatch):
    invalid = {**asdict(WORK), "independent": False, "tmdb_id": 124}
    path = tmp_path / "works.json"
    path.write_text(json.dumps([asdict(WORK), invalid]))
    run = Mock()
    monkeypatch.setattr(candidate_command, "run_candidates", run)
    with pytest.raises(SystemExit):
        candidate_command.main(
            ["--provider", "motn", "--input", str(path), "--max-requests", "2", "--live"]
        )
    assert run.call_count == 0


def test_oversized_batch_is_rejected_before_transport():
    get = Mock()
    with pytest.raises(ValueError, match="exceeds"):
        run_candidates(
            None,
            "motn",
            [WORK, replace(WORK, tmdb_id=124, imdb_id="tt0000124")],
            max_requests=1,
            live=True,
            get=get,
        )
    assert get.call_count == 0


@pytest.mark.parametrize("cap", [True, -1, 1.5, float("inf"), None])
def test_invalid_request_cap_is_not_an_unbounded_mode(cap):
    with pytest.raises(ValueError, match="finite"):
        run_candidates(None, "motn", [WORK], max_requests=cap)
