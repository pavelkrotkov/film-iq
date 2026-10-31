"""The user-facing discovery flow retains registry-only films and typed facts."""

from recognition_support import discovery

from film_iq.discovery_render import markdown
from film_iq.recognition.models import AwardOutcome, ReceptionMetric, Selection


def test_registry_only_pick_is_ready_with_unknown_critic_support(evidence_db):
    report = discovery(evidence_db, Selection("registry_selection", "Fixture Registry", "2025"))
    pick = report["suggested_unwatched"][0]
    assert pick["external_critical_recognition"] is None
    assert pick["evidence_kind"] == "registry_selection"
    assert "critic_selection" in pick["public_evidence_components"]["missing"]
    main, audit = markdown(report).split("<details>", 1)
    assert "Registry selection" in main
    assert "Evidence coverage still unknown" not in main
    assert "critic ballots" in audit and "registry_selection" not in main


def test_person_prize_has_its_recipient_in_the_main_reason(evidence_db):
    report = discovery(
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
    main, audit = markdown(report).split("<details>", 1)
    assert "Fixture Person — Best Actor (prize)" in main
    assert "Best Film" not in main
    assert "event date unknown" in audit and "event date unknown" not in main


def test_reception_units_and_samples_stay_in_the_evidence_audit(evidence_db):
    report = discovery(
        evidence_db, ReceptionMetric("Fixture mean", "critics", "mean", 54, "score_100", 14)
    )
    main, audit = markdown(report).split("<details>", 1)
    assert "54/100; sample count 14" in audit
    assert "sample count" not in main and "Evidence coverage still unknown" not in main
