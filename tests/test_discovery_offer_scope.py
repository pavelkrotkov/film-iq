"""Offer facts only attach to reviewed US works; empty configuration stays unknown."""

from dataclasses import replace

from discovery_offer_support import configure, import_observation, observation, report
from offer_store_support import prepare


def test_other_countries_are_not_us_access(evidence_db, tmp_path):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    source = observation()
    assertions = tuple(
        replace(a, opportunity=replace(a.opportunity, country="CA")) for a in source.assertions
    )
    import_observation(tmp_path, replace(source, country="CA", assertions=assertions))
    assert "offer_states" not in report(tmp_path)["candidates"][0]
    assert "offer_assessed_at" not in report(tmp_path)


def test_zero_policy_database_retains_original_unknown_output(evidence_db, tmp_path):
    configure(evidence_db, tmp_path)
    result = report(tmp_path)
    assert "offer_assessed_at" not in result
    assert (
        result["candidates"][0]["access"] == "unknown; price, entitlement and freshness unverified"
    )


def test_unreviewed_candidate_cannot_inherit_offer_links(evidence_db, tmp_path):
    configure(evidence_db, tmp_path)
    prepare(evidence_db)
    import_observation(tmp_path, observation())
    evidence_db.execute("DELETE FROM current_match")
    evidence_db.commit()
    result = report(tmp_path)
    assert result["candidates"][0]["identity_status"] == "unresolved"
    assert "offer_states" not in result["candidates"][0]
