from dataclasses import replace

import pytest

from film_iq.planning.integration import planner_film
from film_iq.scoring import VERSION, Score


def test_bridge_rejects_invalid_scores_and_crosswalks(evidence_db):
    evidence_db.execute("INSERT INTO film_index (id, tmdb_id) VALUES (42, 1234)")
    result = Score("42", VERSION, 1, None, (), (), 0, 0)
    for invalid in (
        replace(result, film_id="999"),
        replace(result, version="unknown"),
        replace(result, independent_count=0),
    ):
        with pytest.raises(ValueError):
            planner_film(evidence_db, invalid, "Film", 90, False)
    for tmdb_id in (None, 0, -1, "unknown"):
        evidence_db.execute("UPDATE film_index SET tmdb_id = ? WHERE id = 42", (tmdb_id,))
        with pytest.raises(ValueError, match="crosswalk"):
            planner_film(evidence_db, result, "Film", 90, False)
