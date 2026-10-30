"""Replay automated browser truth without promoting the frozen Wikidata leads.

The overlay is an operator attestation, not evidence of calibrated accuracy.
Only complete retrievals with audited truth score; At Land remains excluded.
"""

import copy
import json
from pathlib import Path

from film_iq.identity.evaluation import evaluate

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "identity"


def _apply_overlay(catalog: dict, overlay: dict) -> dict:
    """Patch truth in a disposable copy; leave retrieval and candidates frozen."""
    truths = {case["id"]: case["truth"] for case in overlay["cases"]}
    assert list(truths) == ["la-jetee", "meshes", "night-and-fog", "moon"]
    assert len(overlay["cases"]) == 4
    patched = copy.deepcopy(catalog)
    for case in patched["cases"]:
        case["truth"] = truths.get(case["id"], case["truth"])
    return patched


def _assert_metrics(report: dict) -> None:
    """Check the conditional denominator and overlapping At Land exclusions.

    No accepts means undefined precision, even with all four truth IDs recalled.
    """
    assert report["counts_and_ratios"] == {
        "attempted": 5,
        "scored": 4,
        "unknown_truth": 1,
        "incomplete_retrieval": 1,
        "auto_accepted": 0,
        "correct_auto_accepted": 0,
        "unresolved": 4,
        "truth_in_candidates": 4,
        "precision": None,
        "coverage": 0.0,
        "review_rate": 1.0,
        "candidate_recall": 1.0,
    }
    at_land = report["cases"][-1]
    assert at_land["id"] == "at-land"
    assert (at_land["truth_id"], at_land["scored"]) == (None, False)
    assert at_land["exclusions"] == ["unknown_truth", "incomplete_retrieval"]


def _assert_frozen(patched: dict, catalog: dict) -> None:
    """Removing the truth patch must recover the entire original catalog.

    This also checks that evaluation did not rewrite candidate metadata or
    retrieval provenance while scoring the disposable research input.
    """
    assert patched["cases"][-1] == catalog["cases"][-1]
    for case, frozen in zip(patched["cases"], catalog["cases"], strict=True):
        case["truth"] = frozen["truth"]
    assert patched == catalog


def test_browser_truth_overlay_preserves_frozen_inputs() -> None:
    """Replay saved results and retain original in-memory inputs and file bytes.

    Browser facts supply truth only; the original resolver sees the same frozen
    observations and Wikidata candidates, including their disagreements.
    """
    paths = [FIXTURES / "specialty-observations.json", FIXTURES / "specialty-candidates.json"]
    before = list(map(Path.read_bytes, paths))
    sample, catalog = map(json.loads, before)
    original = copy.deepcopy((sample, catalog))
    overlay = json.loads((FIXTURES / "specialty-browser-truth.json").read_text())
    assert overlay["version"] == sample["version"]
    patched = _apply_overlay(catalog, overlay)
    report = evaluate(sample, patched)
    _assert_metrics(report)
    saved = json.loads((ROOT / "docs" / "identity-browser-audit-results.json").read_text())
    assert report == {key: saved[key] for key in report}
    _assert_frozen(patched, catalog)
    assert (sample, catalog) == original
    assert list(map(Path.read_bytes, paths)) == before
