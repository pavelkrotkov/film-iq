"""Deterministic checks for exact identity, evidence status and source lineage."""

from copy import deepcopy

from review_links import attach_evidence, links_for_film


def main() -> None:
    source = {
        "tmdb_id": 123,
        "identity_status": "reviewed",
        "extraction_status": "accepted",
        "entry_id": "entry-1",
        "revision_id": "rev-1",
        "source_id": "critic-ballot",
        "source_url": "https://example.test/ballot",
        "ballot_scope": "Example critic",
        "evidence_kind": "critic_selection",
        "source_lineage_kind": "derivative",
        "source_lineage": "Derived from a reviewed ballot",
        "edition": "2025",
        "rank": 2,
    }
    component = {
        "tmdb_id": 123,
        "match_decision_id": "match-1",
        "entry_id": "entry-2",
        "revision_id": "rev-2",
        "url": "https://example.test/awards",
        "source_id": "festival",
        "kind": "award_outcome",
        "lineage_kind": "original",
    }
    source["public_evidence_components"] = {"award_outcome": [component], "missing": ["reviews"]}
    pending = {**source, "entry_id": "pending", "extraction_status": "pending_review"}
    other = {**source, "tmdb_id": 124, "entry_id": "other"}
    malformed = {**source, "entry_id": "bad-url", "source_url": "javascript:alert(1)"}
    report = {"candidates": [source, deepcopy(source), pending, other, malformed]}
    before = deepcopy(report)
    result = links_for_film(report, 123)
    assert report == before
    assert result["status"] == "available" and len(result["links"]) == 2
    assert result["links"][0]["kind"] == "critic_selection"
    assert result["links"][0]["lineage_kind"] == "derivative"
    assert result["links"][1]["kind"] == "award_outcome"
    assert links_for_film(report, 999) == {"tmdb_id": 999, "status": "unknown", "links": []}
    manifest = {
        "films": [
            {"tmdb_id": 123, "watched": True, "source_reasons": ["preserve"]},
            {"tmdb_id": 999, "watched": False},
            {"tmdb_id": None, "watched": None},
        ]
    }
    original = deepcopy(manifest)
    joined = attach_evidence(manifest, report)
    assert manifest == original
    assert joined["films"][0]["watched"] and joined["films"][0]["source_reasons"] == ["preserve"]
    assert joined["films"][0]["accepted_discovery_evidence"]["status"] == "available"
    assert joined["films"][1]["accepted_discovery_evidence"]["status"] == "unknown"
    assert joined["films"][2]["accepted_discovery_evidence"]["status"] == "unknown"
    assert attach_evidence(joined, report) == joined
    try:
        links_for_film(report, True)
    except ValueError:
        pass
    else:
        raise AssertionError("boolean is not a film ID")
    print("review-link identity, provenance, unknown, and duplicate checks passed")


if __name__ == "__main__":
    main()
