"""Multiple original reception measurements survive one accepted source entry."""

from recognition_support import accepted_component

from film_iq.recognition import components
from film_iq.recognition.models import ReceptionMetric
from film_iq.recognition.snapshot import replay, save


def test_reception_units_samples_snapshot_and_missingness_are_separate(evidence_db):
    values = (
        ReceptionMetric("Fixture positivity", "critics", "positivity", 87, "percent", 100),
        ReceptionMetric("Fixture mean", "critics", "mean", 54, "score_100", 14),
    )
    accepted_component(evidence_db, values)
    result = components(evidence_db, 123)
    raw = result["reception_metric"][0]["component"]
    assert {(v["value"], v["unit"], v["sample_count"]) for v in raw} == {
        (87, "percent", 100),
        (54, "score_100", 14),
    }
    assert "award_outcome" in result["missing"]
    first = save(evidence_db)
    assert save(evidence_db) == first
    frozen = replay(evidence_db, first)
    assert frozen["critic_results"] == []
    assert frozen["components"][0]["component"] == raw
    evidence_db.execute(
        "DELETE FROM current_extraction WHERE revision_id=?",
        (frozen["components"][0]["revision_id"],),
    )
    assert save(evidence_db) != first
    assert replay(evidence_db, first) == frozen
