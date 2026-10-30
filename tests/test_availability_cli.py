"""The paired CLI keeps one cohort and interleaves both providers without HTTP."""

import json
import sys

from docs.research.availability import run


def test_both_providers_preserve_film_order_and_separate_counts(monkeypatch, tmp_path, capsys):
    cohort = tmp_path / "cohort.json"
    cohort.write_text(json.dumps([{"key": "first"}, {"key": "second"}]))
    output = tmp_path / ".cache" / "paired.json"
    monkeypatch.setattr(run, "ROOT", tmp_path)

    def observe(film, provider, live):
        assert live is True
        return {"key": film["key"], "provider": provider, "requests": 1}

    monkeypatch.setattr(run, "observe", observe)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "availability.run",
            "--cohort",
            str(cohort),
            "--provider",
            "both",
            "--output",
            str(output),
            "--live",
            "--retention-note",
            "fictional provider terms",
        ],
    )
    run.main()
    report = json.loads(output.read_text())
    assert set(report) == {"retention_note", "cohort_sha256", "observations"}
    assert [(row["key"], row["provider"]) for row in report["observations"]] == [
        ("first", "tmdb"),
        ("first", "motn"),
        ("second", "tmdb"),
        ("second", "motn"),
    ]
    assert capsys.readouterr().out == "2 candidates; 4 observations; 4 requests\n"
