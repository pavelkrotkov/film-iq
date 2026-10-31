"""Multiple pending previews remain unaccepted through the actual CLI."""

import json

from discovery_fixtures import cohort

from film_iq.cli import main


def test_discover_cli_combines_distinct_pending_cohorts(tmp_path, capsys):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    records = cohort()
    records["revision_id"] = None
    first.write_text(json.dumps(records))
    records["candidates"][0]["edition"] = "2024"
    second.write_text(json.dumps(records))
    assert (
        main(["discover", "--cohort", str(first), "--cohort", str(second), "--format", "json"]) == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert (report["total_candidates"], report["cohort_count"], report["accepted"]) == (2, 2, 0)
