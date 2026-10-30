"""Check retained CC0 query output against the observed dynamic interface."""

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    receipts = json.loads((root / "receipts.json").read_text())
    browser = json.loads((root / "browser.json").read_text())
    body = (root / "response.json").read_bytes()
    assert hashlib.sha256(body).hexdigest() == receipts["receipts"][1]["sha256"]
    data = json.loads(body)["results"]["bindings"]
    rows = [
        {"qid": row["film"]["value"].rsplit("/", 1)[-1], "label": row["filmLabel"]["value"]}
        for row in data
    ]
    assert rows == browser["rows"] and len(rows) == browser["reported_result_count"]
    assert not any(receipts["receipts"][0]["result_labels_present"].values())
    print(f"{len(rows)} retained API rows match the observed browser table")


if __name__ == "__main__":
    main()
