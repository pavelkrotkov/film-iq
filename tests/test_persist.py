from dataclasses import replace
from pathlib import Path

import pytest

from film_iq.ingest.adapters import film_registry, nbr_2023
from film_iq.ingest.persist import SourcePolicy, persist

FIXTURES = Path(__file__).parent / "fixtures/ingest"
POLICY = SourcePolicy(
    "nbr",
    "NBR",
    "https://nationalboardofreview.org/",
    "awards",
    "nbr",
    "public",
    "metadata",
    "none",
    "cite",
)


def test_provisional_ingestion_is_idempotent(evidence_db):
    db = evidence_db
    result = nbr_2023.extract((FIXTURES / "nbr-2023.wiki").read_bytes())
    rev = persist(db, result, POLICY, "2023", "2026-10-29")
    assert persist(db, result, POLICY, "2023", "2026-10-30") == rev
    assert db.execute(
        "SELECT acceptance_state FROM extraction_revision WHERE id=?", (rev,)
    ).fetchone() == ("pending",)
    assert db.execute(
        "SELECT count(*) FROM entry_observation WHERE revision_id=?", (rev,)
    ).fetchone() == (10,)
    assert (
        db.execute(
            "SELECT rank, tie FROM entry_observation WHERE revision_id=? ORDER BY position", (rev,)
        ).fetchall()
        == [(1, None)] + [(None, None)] * 9
    )
    assert db.execute(
        "SELECT document_revision, original_url FROM extraction_detail WHERE revision_id=?", (rev,)
    ).fetchone() == (result.document_revision, result.original_url)
    assert db.execute(
        "SELECT count(*) FROM current_extraction WHERE revision_id=?", (rev,)
    ).fetchone() == (0,)
    with pytest.raises(ValueError):
        persist(db, result, replace(POLICY, retention=""), "2023", "now")


def test_transcription_stays_pending_and_new_revision_does_not_replace_current(evidence_db):
    db = evidence_db
    result = film_registry.extract(2020, (FIXTURES / "registry/2020.txt").read_bytes())
    policy = replace(
        POLICY,
        id="loc",
        name="LOC",
        url="https://www.loc.gov/programs/national-film-preservation-board/",
    )
    rev = persist(db, result, policy, "2020", "now")
    list_id = db.execute("SELECT list_id FROM extraction_revision WHERE id=?", (rev,)).fetchone()[0]
    # Simulate an independently accepted older revision, not acceptance of the transcription.
    db.execute(
        "INSERT INTO extraction_revision SELECT 'old',source_id,list_id,document_id,run_id,'old','valid','accepted' FROM extraction_revision WHERE id=?",
        (rev,),
    )
    db.execute("INSERT INTO current_extraction (list_id,revision_id) VALUES (?, 'old')", (list_id,))
    db.commit()
    newer = persist(db, replace(result, parser_revision="2"), policy, "2020", "now")
    assert db.execute(
        "SELECT revision_id FROM current_extraction WHERE list_id=?", (list_id,)
    ).fetchone() == ("old",)
    assert db.execute(
        "SELECT acceptance_state FROM extraction_revision WHERE id=?", (newer,)
    ).fetchone() == ("pending",)
    with pytest.raises(ValueError):
        film_registry.extract(2020, b"incomplete")


def test_all_registry_editions_share_one_source(evidence_db):
    db = evidence_db
    policy = replace(
        POLICY,
        id="loc",
        name="LOC",
        url="https://www.loc.gov/programs/national-film-preservation-board/",
    )
    for year in (2020, 2022, 2025):
        result = film_registry.extract(year, (FIXTURES / f"registry/{year}.txt").read_bytes())
        revision = persist(db, result, policy, str(year), "now")
        assert persist(db, result, policy, str(year), "later") == revision
    assert db.execute("SELECT count(*) FROM source WHERE id='loc'").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM published_list WHERE source_id='loc'").fetchone() == (
        3,
    )
    assert db.execute(
        "SELECT count(*) FROM entry_observation WHERE source_id='loc'"
    ).fetchone() == (75,)
    assert db.execute("SELECT count(DISTINCT original_url) FROM extraction_detail").fetchone() == (
        3,
    )
