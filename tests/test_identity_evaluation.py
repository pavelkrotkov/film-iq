"""Denominator checks use synthetic IDs; the real cohort stays unaudited."""

import copy
import json
from pathlib import Path

import pytest

from film_iq.identity.evaluation import evaluate

FIXTURES = Path(__file__).parent / "fixtures" / "identity"


def inputs() -> tuple[dict, dict]:
    """Cover correct, wrong, unresolved, unknown and failed-retrieval cases.

    IDs here are deliberately synthetic; they are not real-world evidence.
    """
    sample = {"version": "synthetic", "cases": []}
    catalog = {"version": "synthetic", "cases": []}
    for number, (truth_id, complete, matches) in enumerate(
        [
            (1, True, True),
            (2, True, True),
            (1, True, False),
            (2, True, False),
            (None, True, True),
            (1, False, True),
        ]
    ):
        sample["cases"].append(
            {
                "id": str(number),
                "stratum": "synthetic",
                "observation": {"title": "Synthetic", "tmdb_id": 1 if matches else 99},
            }
        )
        catalog["cases"].append(
            {
                "id": str(number),
                "retrieval": {"complete": complete},
                "candidates": [{"tmdb_id": 1, "titles": ["Synthetic"]}],
                "truth": {
                    "status": "audited" if truth_id else "unknown",
                    "tmdb_id": truth_id,
                    "reviewer": "synthetic test",
                    "evidence": ["synthetic test only"],
                },
            }
        )
    return sample, catalog


def test_scoring_denominators_and_candidate_misses() -> None:
    """Unknown truth and failed retrieval must not improve precision.

    Candidate recall counts missing truth even when the resolver abstains.
    """
    sample, catalog = inputs()
    # Include one unresolved case whose truth is present and one whose truth is absent.
    report = evaluate(sample, catalog)
    counts = report["counts_and_ratios"]
    assert counts == {
        "attempted": 6,
        "scored": 4,
        "unknown_truth": 1,
        "incomplete_retrieval": 1,
        "auto_accepted": 2,
        "correct_auto_accepted": 1,
        "unresolved": 2,
        "truth_in_candidates": 2,
        "precision": 0.5,
        "coverage": 0.5,
        "review_rate": 0.5,
        "candidate_recall": 0.5,
    }
    assert report["by_method"]["external_id"] == counts
    assert report["by_stratum"]["synthetic"] == counts
    assert report["cases"][4]["match"] == 1
    assert report["cases"][4]["exclusions"] == ["unknown_truth"]
    assert report["cases"][5]["exclusions"] == ["incomplete_retrieval"]


def test_zero_accepts_is_undefined_precision() -> None:
    """Abstention on audited cases gives zero coverage, not zero precision."""
    sample, catalog = inputs()
    for case in sample["cases"]:
        case["observation"]["tmdb_id"] = 99
    counts = evaluate(sample, catalog)["counts_and_ratios"]
    assert counts["precision"] is None
    assert counts["coverage"] == 0
    assert counts["review_rate"] == 1


@pytest.mark.parametrize(
    "change",
    ["missing", "duplicate", "version", "completeness", "unaudited-id", "missing-evidence"],
)
def test_reject_invalid_cohort(change: str) -> None:
    """Reject cohort drift instead of silently truncating or relabeling cases.

    An audit status without evidence cannot turn a lead into scored truth.
    """
    sample, original = inputs()
    catalog = copy.deepcopy(original)
    if change == "missing":
        catalog["cases"].pop()
    if change == "duplicate":
        catalog["cases"].append(catalog["cases"][0])
    if change == "version":
        catalog["version"] = "other"
    if change == "completeness":
        catalog["cases"][0]["retrieval"]["complete"] = "true"
    if change == "unaudited-id":
        catalog["cases"][4]["truth"]["tmdb_id"] = 1
    if change == "missing-evidence":
        catalog["cases"][0]["truth"]["evidence"] = []
    with pytest.raises(ValueError):
        evaluate(sample, catalog)


def test_real_cohort_never_scores_wikidata_as_truth() -> None:
    """Real observations are runnable while independent ID audits are missing.

    Every rate remains undefined until a genuinely audited denominator exists.
    """
    sample = json.loads((FIXTURES / "specialty-observations.json").read_text())
    catalog = json.loads((FIXTURES / "specialty-candidates.json").read_text())
    counts = evaluate(sample, catalog)["counts_and_ratios"]
    assert counts["attempted"] == 5
    assert counts["unknown_truth"] == 5
    assert counts["incomplete_retrieval"] == 1
    assert counts["scored"] == counts["auto_accepted"] == 0
    assert all(
        counts[key] is None for key in ("precision", "coverage", "review_rate", "candidate_recall")
    )
