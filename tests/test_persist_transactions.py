from dataclasses import replace
from pathlib import Path

import pytest

from film_iq.ingest.adapters import nbr_2023
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


@pytest.mark.parametrize("autocommit", [False, True])
def test_transaction_boundaries(evidence_db, autocommit):
    db = evidence_db
    db.commit()
    if autocommit:
        db.isolation_level = None
    else:
        db.execute("BEGIN")
    db.execute("UPDATE source SET name='caller' WHERE id='s'")
    result = nbr_2023.extract((FIXTURES / "nbr-2023.wiki").read_bytes())
    persist(db, result, POLICY, "2023", "now")
    bad = replace(result, parser_revision="2", eligibility="changed")
    with pytest.raises(ValueError, match="published list metadata"):
        persist(db, bad, POLICY, "2023", "later")
    assert db.execute("SELECT name FROM source WHERE id='s'").fetchone() == ("caller",)
    assert db.execute("SELECT count(*) FROM source_run WHERE source_id='nbr'").fetchone() == (1,)
    db.rollback()
    expected = (1,) if autocommit else (0,)
    assert db.execute("SELECT count(*) FROM source WHERE id='nbr'").fetchone() == expected
    name = "caller" if autocommit else "Source"
    assert db.execute("SELECT name FROM source WHERE id='s'").fetchone() == (name,)
