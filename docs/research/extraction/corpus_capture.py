"""Capture licensed versioned Wikipedia sections for a bounded cohort."""

import json
from pathlib import Path

from docs.research.extraction.corpus_http import fetch

ROOT = Path(__file__).parent / "corpus"


def capture(case: dict) -> dict:
    key = case["key"]
    revision, receipt = fetch(
        {
            "action": "query",
            "prop": "revisions",
            "rvprop": "ids|timestamp",
            "titles": case["title"],
        },
        ROOT / f"{key}.revision.json",
    )
    page = next(iter(revision["query"]["pages"].values()))
    oldid = str(page["revisions"][0]["revid"])
    result = case | {"revision": oldid, "revision_receipt": receipt}
    for prop in ("wikitext", "text"):
        _, receipt = fetch(
            {"action": "parse", "oldid": oldid, "section": case["section"], "prop": prop},
            ROOT / f"{key}.{prop}.json",
        )
        result[prop] = receipt
    return result


def main() -> None:
    ROOT.mkdir(exist_ok=True)
    _, rights = fetch(
        {"action": "query", "meta": "siteinfo", "siprop": "rightsinfo"},
        ROOT / "rights.json",
    )
    (ROOT / "rights-receipt.json").write_text(json.dumps(rights, indent=2) + "\n")
    cases = json.loads((ROOT / "selection.json").read_text())
    for case in cases:
        path = ROOT / f"{case['key']}.receipt.json"
        if not path.exists():
            path.write_text(json.dumps(capture(case), indent=2) + "\n")
        print(case["key"], "captured", flush=True)


if __name__ == "__main__":
    main()
