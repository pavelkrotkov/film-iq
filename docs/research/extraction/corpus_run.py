"""Score the frozen static baseline against separate agents' source-only audits."""

import json
from time import perf_counter

from docs.research.extraction.corpus_capture import ROOT
from docs.research.extraction.corpus_metrics import measure
from docs.research.extraction.corpus_parser import extract
from docs.research.extraction.corpus_verify import checked, load_oracles, verify_baseline


def score_case(case: dict, oracle: dict) -> dict:
    receipt = json.loads((ROOT / f"{case['key']}.receipt.json").read_text())
    for kind in ("revision_receipt", "wikitext", "text"):
        checked(ROOT / receipt[kind]["file"], receipt[kind])
    if str(oracle["revision"]) != receipt["revision"]:
        raise ValueError(f"Oracle/source revision mismatch: {case['key']}")
    html = json.loads((ROOT / receipt["text"]["file"]).read_text())["parse"]["text"]["*"]
    started = perf_counter()
    actual = extract(html, case)
    elapsed = perf_counter() - started
    return {
        "key": case["key"],
        "split": case["split"],
        "seconds": elapsed,
        "metrics": measure(oracle["records"], actual),
        "actual": actual,
    }


def run() -> dict:
    freeze = verify_baseline()
    cases = json.loads((ROOT / "selection.json").read_text())
    oracles = load_oracles()
    if set(oracles) != {c["key"] for c in cases}:
        raise ValueError("Incomplete independent oracle cohort")
    return {"baseline": freeze, "cases": [score_case(c, oracles[c["key"]]) for c in cases]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
