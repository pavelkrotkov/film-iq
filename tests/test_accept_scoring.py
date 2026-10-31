"""Synthetic acceptance must make audited, identified original evidence scoreable."""

from fractions import Fraction

from test_accept import AUDIT, pending

from film_iq.ingest.accept import accept
from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence


def test_acceptance_reaches_scoring(evidence_db):
    db = evidence_db
    pending(db)
    # Explicit synthetic classifications, never promotion of captured real sources.
    db.execute(
        "UPDATE source SET name='Synthetic original source', "
        "independence_verification='verified' WHERE id='s'"
    )
    db.execute(
        "UPDATE published_list SET lineage_kind='original', "
        "lineage_verification='verified' WHERE id='list'"
    )
    db.execute("INSERT INTO film_index (id) VALUES (42)")
    db.execute(
        "INSERT INTO match_decision VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("match", "entry", "new", 42, "[]", "synthetic", "1", None, None, "accepted", "now", None),
    )
    db.execute(
        "INSERT INTO current_match (entry_id, revision_id, decision_id, film_id) "
        "VALUES ('entry', 'new', 'match', 42)"
    )
    db.execute("INSERT INTO entry_recognition VALUES ('entry','new','critic_selection','[]',NULL)")
    assert score(load_evidence(db)) == ()

    accept(db, "new", AUDIT, previous_revision_id="rev")

    evidence = load_evidence(db)
    assert len(evidence) == 1
    item = evidence[0]
    assert (item.film_id, item.entry_id, item.revision_id, item.match_decision_id) == (
        "42",
        "entry",
        "new",
        "match",
    )
    assert (item.source_id, item.document_id, item.locator, item.lineage_kind) == (
        "s",
        "doc",
        "#1",
        "original",
    )
    (result,) = score(evidence)
    assert (result.film_id, result.independent_count, result.rank_score) == ("42", 1, Fraction(1))
    assert result.contributing == (item,)
    assert result.excluded == ()
