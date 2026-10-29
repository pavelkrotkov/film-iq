"""Changed responses fail closed; partial aggregates never stand in for ballots."""

import pytest
from test_page_adapters import AUDIT, CASES, PAGES, captured

from film_iq.ingest.adapters import nbr_pages, sight_sound_pages


@pytest.mark.parametrize("key", CASES)
def test_changed_failed_and_partial_responses_require_review(key):
    adapter, year = CASES[key]
    body = (PAGES / f"{key}.json").read_bytes()
    for changed in (b"", b'{"error":{"code":"timeout"}}', body[:-20], body + b" "):
        with pytest.raises(ValueError, match="review required"):
            adapter(year, changed)


@pytest.mark.parametrize("adapter", [nbr_pages.extract, sight_sound_pages.extract])
def test_unreviewed_editions_fail_closed(adapter):
    with pytest.raises(ValueError, match="review required"):
        adapter(2026, b"{}")


def test_partial_aggregate_is_not_a_partial_individual_ballot():
    result = captured("sight-sound-2022")
    assert (
        result.ballot_completeness
        == "not individual ballots; partial aggregate ranking, top ten ranks only"
    )
    assert AUDIT["human_audit"] is False
    assert AUDIT["final_gate_status"]["partial_individual_ballot_present"] is False
