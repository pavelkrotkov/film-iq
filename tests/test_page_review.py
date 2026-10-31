"""Changed responses fail closed; partial aggregates never stand in for ballots."""

from test_page_adapters import AUDIT, captured


def test_partial_aggregate_is_not_a_partial_individual_ballot():
    result = captured("sight-sound-2022")
    assert (
        result.ballot_completeness
        == "not individual ballots; partial aggregate ranking, top ten ranks only"
    )
    assert AUDIT["human_audit"] is False
    assert AUDIT["final_gate_status"]["partial_individual_ballot_present"] is False
