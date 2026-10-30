"""Wholly synthetic extraction boundary case; not a real captured page or ballot."""

from hashlib import sha256

from film_iq.ingest.adapters.page_capture import Entry, Extraction
from film_iq.ingest.persist import SourcePolicy, persist


def test_partial_individual_assessment_preserves_complete_published_content(evidence_db):
    # Invented anonymous ballot: no author is declared, no Film Comment content copied.
    body = b"Synthetic ballot: unranked; US releases in 2025; assessment incomplete.\nSynthetic Film Alpha\nSynthetic Film Beta\n"
    result = Extraction(
        source_url="https://example.test/synthetic-ballot",
        original_url="https://example.test/synthetic-ballot",
        document_revision="synthetic-v1",
        parser_revision="synthetic-extraction-v1",
        content_sha256=sha256(body).hexdigest(),
        eligibility="US releases in 2025",
        ballot_completeness="partial",
        extraction_scope="complete published ballot: both selections; no missing films inferred",
        lineage="wholly synthetic anonymous individual ballot; no real source",
        rank_semantics="unranked; display order is not rank",
        entries=(
            Entry("Synthetic Film Alpha", "Synthetic Film Alpha", 1, None, "line 2", None),
            Entry("Synthetic Film Beta", "Synthetic Film Beta", 2, None, "line 3", None),
        ),
        review_reason="Wholly synthetic semantics test; not audited real-source evidence",
    )
    policy = SourcePolicy(
        "synthetic-ballot",
        "Synthetic ballot",
        result.source_url,
        "individual ballot",
        "synthetic-ballot",
        "synthetic test only; no fetch",
        "synthetic test data",
        "project-authored synthetic data; MIT",
        "film-iq synthetic test",
    )
    revision = persist(evidence_db, result, policy, "2025", "2026-10-29T00:00:00Z")
    assert evidence_db.execute(
        "SELECT author,eligibility,completeness,rank_semantics FROM published_list WHERE source_id=?",
        (policy.id,),
    ).fetchone() == (None, result.eligibility, result.ballot_completeness, result.rank_semantics)
    assert evidence_db.execute(
        "SELECT raw_title,raw_context,position,rank,tie,locator FROM entry_observation WHERE revision_id=? ORDER BY position",
        (revision,),
    ).fetchall() == [
        ("Synthetic Film Alpha", "Synthetic Film Alpha", 1, None, None, "line 2"),
        ("Synthetic Film Beta", "Synthetic Film Beta", 2, None, None, "line 3"),
    ]
    assert evidence_db.execute(
        "SELECT extraction_scope,document_revision FROM extraction_detail WHERE revision_id=?",
        (revision,),
    ).fetchone() == (result.extraction_scope, result.document_revision)
    before = evidence_db.total_changes
    assert persist(evidence_db, result, policy, "2025", "2026-10-30T00:00:00Z") == revision
    assert evidence_db.total_changes == before
