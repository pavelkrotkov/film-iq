"""C1's explicit contributor and derivative links reach the scoring boundary."""

from test_scoring_a1 import accepted

from film_iq.ingest.ballots import link_entry, record_ballot
from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence


def test_reviewed_person_link_does_not_use_author_text(evidence_db):
    db = evidence_db
    accepted(db)
    record_ballot(db, "ballot", "list", "named ballot", contributor_id="person:1")
    link_entry(db, "entry", "ballot")
    item = load_evidence(db)[0]
    result = score([item])[0]
    assert item.person_id == "person:1" and item.author == "Critic"
    assert (result.known_person_count, result.unknown_contributor_count) == (1, 0)


def test_derivative_ballot_link_excludes_original_classified_list(evidence_db):
    db = evidence_db
    accepted(db)
    record_ballot(db, "original", "list", "original ballot")
    record_ballot(db, "copy", "list", "reprinted ballot", original_ballot_id="original")
    link_entry(db, "entry", "copy")
    item = load_evidence(db)[0]
    result = score([item])[0]
    assert item.derivative_of == ("original",) and item.lineage_kind == "original"
    assert (result.independent_count, result.rank_score, result.excluded) == (0, None, (item,))
