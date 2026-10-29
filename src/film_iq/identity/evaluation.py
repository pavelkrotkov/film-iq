"""Offline measurement of frozen observations; unaudited truth never scores.

Run: uv run python -m film_iq.identity.evaluation OBSERVATIONS CANDIDATES
The JSON inputs are research records, not provider API responses.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from . import Candidate, Observation, resolve


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _metrics(rows: list[dict]) -> dict:
    scored = [row for row in rows if row["scored"]]
    accepted = [row for row in scored if row["match"] is not None]
    correct = sum(row["match"] == row["truth_id"] for row in accepted)
    recalled = sum(row["truth_id"] in row["candidate_ids"] for row in scored)
    return {
        "attempted": len(rows),
        "scored": len(scored),
        **_exclusions(rows),
        "auto_accepted": len(accepted),
        "correct_auto_accepted": correct,
        "unresolved": len(scored) - len(accepted),
        "truth_in_candidates": recalled,
        "precision": _ratio(correct, len(accepted)),
        "coverage": _ratio(len(accepted), len(scored)),
        "review_rate": _ratio(len(scored) - len(accepted), len(scored)),
        "candidate_recall": _ratio(recalled, len(scored)),
    }


def _exclusions(rows: list[dict]) -> dict:
    return {
        label: sum(label in row["exclusions"] for row in rows)
        for label in ("unknown_truth", "incomplete_retrieval")
    }


def _truth(record: dict) -> int | None:
    truth = record["truth"]
    if truth["status"] == "unknown":
        if truth["tmdb_id"] is not None:
            raise ValueError("Unknown truth must have a null ID")
        return None
    if truth["status"] != "audited" or not truth.get("reviewer") or not truth.get("evidence"):
        raise ValueError("Audited truth requires status, reviewer and evidence")
    if type(truth["tmdb_id"]) is not int or truth["tmdb_id"] <= 0:
        raise ValueError("Audited truth requires a positive TMDB ID")
    return truth["tmdb_id"]


def _evaluate(case: dict, record: dict) -> dict:
    complete = record["retrieval"]["complete"]
    if type(complete) is not bool:
        raise ValueError("Retrieval completeness must be explicit boolean")
    truth_id = _truth(record)
    candidates = tuple(
        Candidate(
            c["tmdb_id"], tuple(c["titles"]), c.get("director"), c.get("year"), c.get("imdb_id")
        )
        for c in record["candidates"]
    )
    decision = resolve(Observation(**case["observation"]), candidates)
    return {
        "id": case["id"],
        "stratum": case["stratum"],
        "method": decision.method,
        "candidate_ids": list(decision.candidates),
        "match": decision.match,
        "truth_id": truth_id,
        "truth_status": record["truth"]["status"],
        "retrieval_complete": complete,
        "scored": truth_id is not None and complete,
        "exclusions": [
            label
            for label, excluded in (
                ("unknown_truth", truth_id is None),
                ("incomplete_retrieval", not complete),
            )
            if excluded
        ],
    }


def evaluate(sample: dict, catalog: dict) -> dict:
    """Score only independently audited truth and complete retrievals.

    Audit status is an operator attestation: evidence must be reviewed separately.
    A complete Wikidata search is not a complete TMDB catalog search.
    """
    observations = {case["id"]: case for case in sample["cases"]}
    records = {case["id"]: case for case in catalog["cases"]}
    if len(observations) != len(sample["cases"]) or len(records) != len(catalog["cases"]):
        raise ValueError("Duplicate case IDs")
    if observations.keys() != records.keys() or sample["version"] != catalog["version"]:
        raise ValueError("Candidate cohort must exactly match frozen observations and version")
    rows = [_evaluate(case, records[key]) for key, case in observations.items()]
    return {
        "dataset_version": sample["version"],
        "scope": "Resolver conditional on supplied retrieval policy; not population precision",
        "counts_and_ratios": _metrics(rows),
        "by_method": _groups(rows, "method"),
        "by_stratum": _groups(rows, "stratum"),
        "cases": rows,
    }


def _groups(rows: list[dict], key: str) -> dict:
    return {
        value: _metrics([row for row in rows if row[key] == value])
        for value in sorted({row[key] for row in rows})
    }


def main() -> None:
    paths = [Path(argument) for argument in sys.argv[1:]]
    if len(paths) != 2:
        raise SystemExit("Usage: python -m film_iq.identity.evaluation OBSERVATIONS CANDIDATES")
    contents = [path.read_bytes() for path in paths]
    report = evaluate(*(json.loads(content) for content in contents))
    report["input_sha256"] = {
        str(path): hashlib.sha256(content).hexdigest()
        for path, content in zip(paths, contents, strict=True)
    }
    report["code_revision"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    report["code_sha256"] = {
        name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ("evaluation.py", "matching.py", "models.py")
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
