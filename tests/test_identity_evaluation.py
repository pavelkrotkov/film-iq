"""Denominator checks use synthetic IDs; the real cohort stays unaudited."""

from pathlib import Path

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
