import json
from dataclasses import asdict
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


def test_uncertainty_is_explicit_for_accepted_evidence_and_v1_replay(evidence_db):
    db = evidence_db
    accepted(db)
    result = score(load_evidence(db))[0]
    expected = {
        "extraction_uncertainty": "not_evaluated",
        "identity_uncertainty": "not_evaluated",
        "evidence_disagreement_uncertainty": "not_evaluated",
        "prediction_uncertainty": "not_applicable",
    }
    # Existing Fraction/date output conversion belongs to the report layer.
    serialized = json.loads(json.dumps({key: asdict(result)[key] for key in expected}))
    assert serialized == expected
    initialize(db)
    current_id = save(db, load_evidence(db), "now")
    assert replay(db, current_id) == (result,)

    # Literal payload and ID captured from v1 before uncertainty fields existed.
    legacy_id = "32446dfdb8f371f983ebe031749fd18fee39840a840bede5a690f29026e5ab97"
    payload = (
        '[{"derivative_of":[],"eligibility":"eligible","entry_id":null,"film_id":"42",'
        '"independence_group":"critic","list_id":"list","match_decision_id":null,'
        '"published":null,"rank":1,"revision_id":null,"url":"https://example.test/list"}]'
    )
    db.execute(
        "INSERT INTO scoring_snapshot VALUES (?, ?, ?, ?)",
        (legacy_id, "independent-reciprocal-rank-v1", "before", payload),
    )
    legacy_evidence = [
        Evidence("42", "list", "https://example.test/list", None, "critic", "eligible", 1)
    ]
    legacy_result = replay(db, legacy_id)[0]
    assert legacy_result == score(legacy_evidence)[0]
    assert {key: asdict(legacy_result)[key] for key in expected} == expected
    assert (legacy_result.independent_count, legacy_result.rank_score) == (1, 1)
    assert save(db, legacy_evidence, "later") == legacy_id
