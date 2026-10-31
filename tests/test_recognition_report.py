"""Actual accepted source facts reach the report without fabricated critic utility."""

from recognition_support import accepted_component
from test_report import inputs

from film_iq.recognition.models import AwardOutcome, ReceptionMetric, Selection
from film_iq.report import build_report
from film_iq.report_render import markdown


def test_registry_only_discovery_is_visible_without_critic_count(evidence_db):
    accepted_component(evidence_db, Selection("registry_selection", "Fixture Registry", "2025"))
    report = build_report(evidence_db, inputs())
    assert report["evidence"] == []
    rendered = markdown(report)
    assert "Registry selection: Fixture Registry, 2025" in rendered
    assert "critic ballots" in rendered and "unknown" in rendered
    assert "https://example.test/list" in rendered


def test_person_award_preserves_subject_and_unknown_ceremony(evidence_db):
    accepted_component(
        evidence_db,
        AwardOutcome(
            "Fixture Academy",
            None,
            "Best Actor",
            "prize",
            recipient="Fixture Person",
            recipient_kind="person",
        ),
    )
    rendered = markdown(build_report(evidence_db, inputs()))
    assert "Best Actor — prize; recipient Fixture Person (person)" in rendered
    assert "event date unknown" in rendered and "edition unknown" in rendered
    assert "Best Film" not in rendered


def test_reception_original_value_unit_sample_and_missing_awards_render(evidence_db):
    accepted_component(
        evidence_db, ReceptionMetric("Fixture mean", "critics", "mean", 54, "score_100", 14)
    )
    report = build_report(evidence_db, inputs())
    rendered = markdown(report)
    assert report["evidence"] == []
    assert "Fixture mean (critics, mean): 54/100; sample count 14" in rendered
    assert "measured unknown" in rendered and "awards" in rendered
