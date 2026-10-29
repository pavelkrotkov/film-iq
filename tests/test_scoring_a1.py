from datetime import date

from film_iq.scoring import Evidence, score
from film_iq.scoring.a1 import load_evidence
from film_iq.scoring.snapshot import initialize, replay, save


def accepted(db):
    db.execute("UPDATE source SET independence_verification = 'verified'")
    db.execute(
        "UPDATE published_list SET lineage_verification = 'verified', lineage_kind = 'original'"
    )
    db.execute("INSERT INTO film_index (id) VALUES (42)")
    db.execute(
        "INSERT INTO match_decision VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("match", "entry", "rev", 42, "[]", "manual", "1", None, None, "accepted", "now", None),
    )
    db.execute("INSERT INTO current_extraction (list_id, revision_id) VALUES ('list', 'rev')")
    db.execute(
        "INSERT INTO current_match (entry_id, revision_id, decision_id, film_id) VALUES ('entry', 'rev', 'match', 42)"
    )


def test_current_verified_evidence_and_snapshot(evidence_db):
    db = evidence_db
    accepted(db)
    expected = Evidence(
        "42",
        "list",
        "https://example.test/list",
        None,
        "original",
        "released in 2025",
        1,
        entry_id="entry",
        revision_id="rev",
        match_decision_id="match",
        source_id="s",
        document_id="doc",
        locator="#1",
        lineage_kind="original",
        lineage="original",
        author="Critic",
        completeness="partial",
        rank_semantics="ranked",
    )
    assert load_evidence(db) == [expected]
    initialize(db)
    snapshot_id = save(db, load_evidence(db), "now")
    db.execute("UPDATE source SET independence_verification = 'unknown'")
    assert load_evidence(db) == []
    assert replay(db, snapshot_id) == score([expected])
    db.execute("UPDATE source SET independence_verification = 'verified'")
    db.execute("UPDATE source_document SET published_at = '2025-12-31T12:00:00Z'")
    assert load_evidence(db)[0].published == date(2025, 12, 31)


def test_excludes_unverified_nonoriginal_and_noncurrent(evidence_db):
    db = evidence_db
    accepted(db)
    for statement in (
        "UPDATE source SET independence_verification = 'unknown'",
        "UPDATE source SET independence_verification = 'disputed'",
        "UPDATE source SET independence_group = ''",
        "UPDATE published_list SET lineage_verification = 'unknown'",
        "UPDATE published_list SET lineage_verification = 'disputed'",
        "UPDATE published_list SET lineage_kind = 'unknown'",
        "UPDATE entry_observation SET extraction_decision = 'rejected'",
        "DELETE FROM current_match",
        "DELETE FROM current_extraction",
    ):
        db.execute("SAVEPOINT check_exclusion")
        db.execute(statement)
        assert load_evidence(db) == [], statement
        db.execute("ROLLBACK TO check_exclusion")
        db.execute("RELEASE check_exclusion")
