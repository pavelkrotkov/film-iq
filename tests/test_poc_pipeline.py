"""Wholly synthetic integration evidence; this does not establish the real Gate A."""

from hashlib import sha256

import pytest
from e2e.stub_backend import StubBackend
from test_accept import AUDIT
from test_report import inputs

from film_iq.approval import Preview, sync_one
from film_iq.identity import Candidate, Observation, resolve, review, save
from film_iq.ingest.accept import accept
from film_iq.ingest.adapters.page_capture import Entry, Extraction
from film_iq.ingest.persist import SourcePolicy, persist
from film_iq.report import build_report
from film_iq.storage import connect, migrate

TITLE = "Fixture film"
URL = "https://example.test/synthetic-original"
EXTRACTION = Extraction(
    source_url=URL,
    original_url=URL,
    document_revision="synthetic-1",
    parser_revision="synthetic-1",
    content_sha256=sha256(TITLE.encode()).hexdigest(),
    eligibility="Synthetic one-film selection",
    ballot_completeness="complete",
    extraction_scope="Entire synthetic list",
    lineage="Synthetic original source, not a captured Wikipedia fixture",
    rank_semantics="ranked",
    entries=(Entry(TITLE, TITLE, 1, 1, "#1", None),),
    review_reason="Synthetic audit required",
)
POLICY = SourcePolicy(
    "synthetic",
    "Synthetic original",
    URL,
    "poll",
    "synthetic",
    "synthetic public input",
    "synthetic metadata",
    "CC0 synthetic data",
    "test author",
)


def _accept_synthetic(db):
    revision = persist(db, EXTRACTION, POLICY, "2026", AUDIT.audited_at)
    # These classifications apply only to newly constructed synthetic evidence.
    db.execute("UPDATE source SET independence_verification='verified' WHERE id='synthetic'")
    db.execute(
        "UPDATE published_list SET lineage_kind='original', lineage_verification='verified' "
        "WHERE source_id='synthetic'"
    )
    assert build_report(db, inputs())["evidence"] == []
    accept(db, revision, AUDIT, previous_revision_id=None)
    (entry_id,) = db.execute(
        "SELECT entry_id FROM entry_observation WHERE revision_id=?", (revision,)
    ).fetchone()
    return revision, entry_id


def _identify(db, revision, entry_id):
    (title,) = db.execute(
        "SELECT raw_title FROM entry_observation WHERE entry_id=? AND revision_id=?",
        (entry_id, revision),
    ).fetchone()
    db.execute("INSERT INTO film_index (id, tmdb_id) VALUES (42, 1)")
    decision = resolve(Observation(title), (Candidate(1, (title,)),))
    assert decision.match is None  # Title alone cannot establish identity.
    automatic = save(db, entry_id, revision, decision)
    reviewed = review((decision,), 1, "Synthetic reviewer", "Synthetic candidate confirmed")[1]
    match = save(db, entry_id, revision, reviewed, automatic)
    return decision, automatic, match


def _selected_preview(report, revision, entry_id, match):
    (score,) = report["evidence"]
    (evidence,) = score["contributing"]
    assert (evidence["revision_id"], evidence["entry_id"], evidence["match_decision_id"]) == (
        revision,
        entry_id,
        match,
    )
    assert (score["film_id"], score["independent_count"], evidence["url"]) == ("42", 1, URL)
    assert report["crosswalk"] == {"42": 1}
    assert report["offers"][0]["status"] == "complete"
    plan = report["plans"][0]
    (choice,) = plan["choices"]
    assert (plan["option"], plan["cost_cents"], plan["utility"]) == ("no purchase", 0, 1.0)
    assert (choice["offer"]["kind"], choice["offer"]["entitlement"]) == ("free", "unconfirmed")
    return Preview(choice["film"]["title"], choice["film"]["id"])


def test_synthetic_source_to_approved_watchlist_and_unchanged_rerun(tmp_path):
    db = connect(tmp_path / "pipeline.db")
    migrate(db)
    revision, entry_id = _accept_synthetic(db)
    decision, automatic, match = _identify(db, revision, entry_id)
    db.commit()
    before = tuple(db.iterdump())
    changes = db.total_changes
    report = build_report(db, inputs())
    preview = _selected_preview(report, revision, entry_id, match)
    backend = StubBackend()
    assert sync_one(preview, backend) == report["previews"]["no purchase"][0]
    with pytest.raises(PermissionError, match="explicit approval"):
        sync_one(preview, backend, execute=True)
    assert (report["mode"], tuple(db.iterdump()), db.total_changes, backend.writes) == (
        "dry-run",
        before,
        changes,
        [],
    )
    assert sync_one(preview, backend, execute=True, approved=True) == "added to watchlist"

    # The audit/review are one-time explicit decisions; replay automatic work only.
    assert (
        persist(db, EXTRACTION, POLICY, "2026", "2026-10-30T00:00:00Z"),
        save(db, entry_id, revision, decision),
    ) == (revision, automatic)
    assert build_report(db, inputs()) == report
    assert sync_one(preview, backend, execute=True, approved=True) == "already on watchlist"
    assert (tuple(db.iterdump()), db.total_changes, backend.writes, backend.watchlist) == (
        before,
        changes,
        [("movie", 1), ("watchlist", 456)],
        {99, 456},
    )
    db.close()
