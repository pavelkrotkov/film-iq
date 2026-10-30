"""Real captures stay pending and preserve tied ranks across unchanged reruns."""

from dataclasses import replace

import pytest
from test_page_adapters import AUDIT, CASES, captured

from film_iq.ingest.persist import SourcePolicy, persist

POLICY = SourcePolicy(
    "wikipedia-bfi-directors",
    "Wikipedia contributors' derivative selections",
    "https://en.wikipedia.org/",
    "critical selections",
    "bfi-directors",
    "public MediaWiki API",
    "CC BY-SA 4.0 text captures; no image bytes",
    "CC BY-SA 4.0 with attribution",
    "Wikipedia contributors; revision/history URLs in fixture notices",
)


@pytest.mark.parametrize("key", CASES)
def test_real_capture_persistence_is_pending_and_idempotent(evidence_db, key):
    result = captured(key)
    policy = replace(POLICY, id=key, independence_group=key.rsplit("-", 1)[0])
    revision = persist(evidence_db, result, policy, key, "2026-10-29T22:07:27Z")
    before = evidence_db.total_changes
    assert persist(evidence_db, result, policy, key, "2026-10-30T00:00:00Z") == revision
    assert evidence_db.total_changes == before
    rows = evidence_db.execute(
        "SELECT raw_title,position,rank,tie FROM entry_observation WHERE revision_id=? ORDER BY position",
        (revision,),
    ).fetchall()
    expected = next(page["expected_entries"] for page in AUDIT["per_page"] if page["key"] == key)
    assert rows == [(row["title"], row["position"], row["rank"], row["tie"]) for row in expected]


def test_real_capture_does_not_become_accepted_by_test_oracle(evidence_db):
    result = captured("sight-sound-2022")
    revision = persist(evidence_db, result, POLICY, "2022", "2026-10-29T22:07:27Z")
    assert evidence_db.execute(
        "SELECT validation_state,acceptance_state FROM extraction_revision WHERE id=?", (revision,)
    ).fetchone() == ("provisional", "pending")
    assert (
        evidence_db.execute(
            "SELECT revision_id FROM current_extraction WHERE revision_id=?", (revision,)
        ).fetchone()
        is None
    )
    assert evidence_db.execute(
        "SELECT completeness,rank_semantics FROM published_list WHERE source_id=?", (POLICY.id,)
    ).fetchone() == (result.ballot_completeness, result.rank_semantics)
