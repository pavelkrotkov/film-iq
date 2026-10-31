"""Only reviewed display attribution is exposed, never private rights evidence."""

from dataclasses import replace

from discovery_offer_support import configure, import_observation, observation, report
from offer_store_support import NOW, policy

from film_iq.availability.policies import record_policy


def test_registered_source_credit_is_visible_without_rights_notes(evidence_db, tmp_path):
    configure(evidence_db, tmp_path)
    record_policy(
        evidence_db,
        replace(
            policy(allowed=True),
            attribution="[Fixture API](https://example.test/api)",
            rights_evidence="PRIVATE synthetic rights note",
        ),
        NOW,
    )
    import_observation(tmp_path, observation())
    output = report(tmp_path, output_format="markdown")
    assert "Credits: [Fixture API](https://example.test/api)" in output
    assert "PRIVATE synthetic rights note" not in output

    assert output.index("Credits:") < output.index("<details>")
    assert output.count("Credits:") == 1
