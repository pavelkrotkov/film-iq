"""One historical government PDF page; exact-field comparison, no ranking claim."""

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
ROW = re.compile(r"^(.+) (\d{4}(?:s-\d{4}s)?) (\d{4})$", re.MULTILINE)


def extract(text: str) -> list[dict]:
    return [
        {
            "title": match[1],
            "year_released": match[2],
            "year_inducted": match[3],
            "position": position,
            "rank": None,
            "category": "National Film Registry selections 1989–2017",
        }
        for position, match in enumerate(ROW.finditer(text), 1)
    ]


def main() -> None:
    started = time.perf_counter()
    try:
        receipt = json.loads((ROOT / "source_receipt.json").read_text())
        pdf = ROOT / "registry-page1.pdf"
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != receipt["retained_page_sha256"]:
            raise ValueError("changed page requires new audit")
        payload = (ROOT / "registry-page1.text.json").read_text()
        if "--snapshot" not in sys.argv:
            payload = subprocess.check_output(
                ["osascript", "-l", "JavaScript", str(ROOT / "pdf_text.js"), str(pdf)], text=True
            )
        rows = extract(json.loads(payload)["text"])
        expected = json.loads((ROOT / "pdf_audit.json").read_text())["records"]
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "unknown", "reason": str(error)}))
        raise SystemExit(2) from error
    complete = rows == expected
    print(
        json.dumps(
            {
                "extracted": len(rows),
                "expected": len(expected),
                "exact_fields": complete,
                "seconds": round(time.perf_counter() - started, 6),
            }
        )
    )
    assert extract("Incomplete row") == [] and extract("") == []
    assert rows[:-1] != expected  # An omitted row must fail exact completeness.
    raise SystemExit(0 if complete else 1)


if __name__ == "__main__":
    main()
