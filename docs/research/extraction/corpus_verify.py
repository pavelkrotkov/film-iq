"""Verify frozen parser and source-byte provenance before evaluation."""

import hashlib
import json
from pathlib import Path

from docs.research.extraction.corpus_capture import ROOT


def checked(path: Path, receipt: dict) -> bytes:
    raw = path.read_bytes()
    if len(raw) != receipt["bytes"] or hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
        raise ValueError(f"Changed captured bytes: {path.name}; status unknown")
    return raw


def verify_baseline() -> dict:
    freeze = json.loads((ROOT / "baseline-freeze.json").read_text())
    for name, expected in freeze["files"].items():
        if hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen baseline changed: {name}")
    return freeze


def load_oracles() -> dict:
    audits = [json.loads(p.read_text()) for p in sorted(ROOT.glob("audit*.json"))]
    oracles = {c["key"]: c for audit in audits for c in audit["per_case"]}
    if len(oracles) != sum(len(a["per_case"]) for a in audits):
        raise ValueError("Duplicated independent oracle cases")
    return oracles
