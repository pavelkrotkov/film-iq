import sqlite3

import pytest

from film_iq.ingest.ballots import link_entry, record_ballot


def test_ballot_lineage_unknown_identity_and_idempotence(evidence_db):
    db = evidence_db
    record_ballot(
        db,
        "original",
        "list",
        "ranked complete ballot",
        contributor_id="critic-1",
        contributor_name="Synthetic Critic",
    )
    record_ballot(
        db,
        "original",
        "list",
        "ranked complete ballot",
        contributor_id="critic-1",
        contributor_name="Synthetic Critic",
    )
    record_ballot(db, "quoted", "list", "partial derivative", original_ballot_id="original")
    record_ballot(db, "unknown", "list", "unranked partial ballot")
    link_entry(db, "entry", "original")
    link_entry(db, "entry", "original")
    assert db.execute("SELECT contributor_id FROM source_ballot WHERE id='unknown'").fetchone() == (
        None,
    )
    assert db.execute(
        "SELECT original_ballot_id FROM source_ballot WHERE id='quoted'"
    ).fetchone() == ("original",)
    assert db.execute("SELECT count(*) FROM entry_ballot").fetchone() == (1,)
    with pytest.raises(ValueError, match="differs"):
        record_ballot(db, "original", "list", "silently changed")
    with pytest.raises(ValueError, match="different"):
        link_entry(db, "entry", "quoted")


def test_ballot_and_entry_list_must_agree(evidence_db):
    db = evidence_db
    record_ballot(db, "one", "list", "unranked")
    db.execute(
        "INSERT INTO published_list (id,source_id,edition,author,eligibility,period,rank_semantics,completeness,lineage) SELECT 'another',source_id,'new',author,eligibility,period,rank_semantics,completeness,lineage FROM published_list WHERE id='list'"
    )
    db.execute("INSERT INTO list_entry VALUES ('other','s','another','1')")
    with pytest.raises(sqlite3.IntegrityError):
        link_entry(db, "other", "one")
    with pytest.raises(ValueError, match="itself"):
        record_ballot(db, "self", "list", "scope", original_ballot_id="self")
    with pytest.raises(ValueError, match="required"):
        record_ballot(db, "", "list", "scope")
