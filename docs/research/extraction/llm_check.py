"""Check quoted source spans separately from scoped semantic membership."""

import json

from docs.research.extraction.corpus_capture import ROOT
from docs.research.extraction.corpus_metrics import FIELDS, measure
from docs.research.extraction.corpus_verify import checked


def normalized(record: dict) -> dict:
    result = {field: record[field] for field in FIELDS}
    if result["tie"] is False:
        result["tie"] = None
    if record.get("subcategory") == "Closest runner-up":
        result["category"] = "Closest runner-up"
    return result


def run() -> dict:
    output = json.loads((ROOT.parent / "llm_poll0.json").read_text())
    receipt = json.loads((ROOT / "poll-0.receipt.json").read_text())
    raw = checked(ROOT / receipt["wikitext"]["file"], receipt["wikitext"])
    lines = json.loads(raw)["parse"]["wikitext"]["*"].splitlines()
    spans = [check_span(record["evidence"], lines) for record in output["records"]]
    audit = json.loads((ROOT / "audit_group2.json").read_text())
    expected = next(c for c in audit["per_case"] if c["key"] == "poll-0")["records"]
    return {
        "valid_spans": sum(spans),
        "total_spans": len(spans),
        "metrics": measure(expected, [normalized(r) for r in output["records"]]),
    }


def check_span(evidence: dict, lines: list[str]) -> bool:
    if evidence["source_file"] != "corpus/poll-0.wikitext.json":
        return False
    excerpt = "\n".join(lines[evidence["line_start"] - 1 : evidence["line_end"]])
    return evidence["quote"] in excerpt


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
