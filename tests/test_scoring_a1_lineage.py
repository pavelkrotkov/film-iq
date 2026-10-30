from test_scoring_a1 import accepted

from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence
from film_iq.scoring.snapshot import initialize, replay, save


def assert_derivative(result):
    derivative = result.excluded[0]
    assert (derivative.lineage_kind, derivative.lineage, derivative.derivative_of) == (
        "derivative",
        "reported aggregate",
        (),
    )
    assert (derivative.source_id, derivative.document_id, derivative.entry_id) == (
        "s2",
        "doc2",
        "entry2",
    )


def test_derivative_and_corrected_list_context_survive_snapshot(evidence_db):
    db = evidence_db
    accepted(db)
    db.execute(
        "INSERT INTO source SELECT 's2', name, family, 'aggregate', url, country, cadence, access_policy, retention_policy, redistribution_policy, attribution, health, independence_verification FROM source WHERE id = 's'"
    )
    db.execute(
        "INSERT INTO source_run SELECT 'run2', 's2', started_at, finished_at, outcome, parser_version, error, last_success_at FROM source_run WHERE id = 'run'"
    )
    db.execute(
        "INSERT INTO source_document SELECT 'doc2', 's2', url, content_hash, accessed_at, published_at, fetch_state, retention_policy FROM source_document WHERE id = 'doc'"
    )
    db.execute(
        "INSERT INTO published_list SELECT 'list2', 's2', edition, 'Editor', eligibility, period, rank_semantics, completeness, 'reported aggregate', lineage_verification, 'derivative' FROM published_list WHERE id = 'list'"
    )
    db.execute(
        "INSERT INTO extraction_revision SELECT 'rev2', 's2', 'list2', 'doc2', 'run2', extractor_version, validation_state, acceptance_state FROM extraction_revision WHERE id = 'rev'"
    )
    db.execute(
        "INSERT INTO list_entry SELECT 'entry2', 's2', 'list2', entry_key FROM list_entry WHERE id = 'entry'"
    )
    db.execute(
        "INSERT INTO entry_observation SELECT 'entry2', 's2', 'list2', 'rev2', raw_title, raw_context, original_title, listed_year, director, position, rank, tie, locator, extraction_decision, raw_imdb_id, raw_tmdb_id FROM entry_observation WHERE entry_id = 'entry'"
    )
    db.execute(
        "INSERT INTO match_decision SELECT 'match2', 'entry2', 'rev2', film_id, candidates, method, version, confidence, reviewer, decision, decided_at, supersedes FROM match_decision WHERE id = 'match'"
    )
    db.execute("INSERT INTO current_extraction (list_id, revision_id) VALUES ('list2', 'rev2')")
    db.execute(
        "INSERT INTO current_match (entry_id, revision_id, decision_id, film_id) VALUES ('entry2', 'rev2', 'match2', 42)"
    )

    initialize(db)
    evidence = load_evidence(db)
    snapshot_id = save(db, evidence, "now")
    result = replay(db, snapshot_id)[0]
    assert (result.independent_count, result.rank_score) == (1, 1)
    assert (result.unranked_count, result.partial_count) == (0, 1)
    assert_derivative(result)
    db.execute(
        "UPDATE published_list SET author = 'Corrected', completeness = 'complete', rank_semantics = 'unranked' WHERE id = 'list'"
    )
    corrected = load_evidence(db)
    assert save(db, corrected, "later") != snapshot_id
    assert replay(db, snapshot_id) == score(evidence)
    assert (
        result.contributing[0].author,
        result.contributing[0].completeness,
        result.contributing[0].rank_semantics,
    ) == ("Critic", "partial", "ranked")
    assert score(corrected)[0].partial_count == 0
