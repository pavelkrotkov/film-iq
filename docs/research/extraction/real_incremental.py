"""Replay two audited NBR editions through persistent loaders, without live polling."""

import json
from pathlib import Path
from uuid import uuid4

from docs.research.extraction.comparison_data import run_sqlite
from docs.research.extraction.corpus_capture import ROOT
from docs.research.extraction.corpus_verify import checked
from docs.research.extraction.dlt_comparison import prepare, run_dlt


def source_rows(key: str) -> list[tuple[str, str]]:
    audit = json.loads((ROOT / "audit_group1.json").read_text())
    case = next(c for c in audit["per_case"] if c["key"] == key)
    receipt = json.loads((ROOT / f"{key}.receipt.json").read_text())
    if str(case["revision"]) != receipt["revision"]:
        raise ValueError(f"Oracle/source revision mismatch: {key}")
    checked(ROOT / receipt["text"]["file"], receipt["text"])
    return [(f"{key}:{r['position']:03}", r["title"]) for r in case["records"]]


def main() -> None:
    initial = source_rows("nbr-0")
    added = source_rows("nbr-1")
    root = Path(__file__).resolve().parents[3] / ".cache" / "real-incremental" / uuid4().hex
    prepare(root)
    print("initial_records", len(initial), "added_records", len(added), "root", root)
    # Replay new edition first so the injected failure follows an actual new record.
    run_sqlite(root, initial, added + initial)
    run_dlt(root, initial, added + initial)


if __name__ == "__main__":
    main()
