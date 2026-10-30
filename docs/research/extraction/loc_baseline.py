"""Opt-in live check against one manually transcribed source revision."""

import json
from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from urllib.error import URLError
from urllib.request import Request, urlopen

from docs.research.extraction.loc_parser import extract_titles


def evaluate(body: bytes, expected: list[str], revision: str) -> dict[str, object]:
    if sha256(body).hexdigest() != revision:
        raise ValueError("Source revision changed; re-audit before comparing")
    if not expected:
        raise ValueError("Expected entries cannot be empty")
    actual = extract_titles(body.decode("utf-8"))
    matches = sum((Counter(expected) & Counter(actual)).values())
    return {
        "expected": len(expected),
        "extracted": len(actual),
        "precision": matches / len(actual) if actual else None,
        "recall": matches / len(expected),
        "complete": len(actual) == len(expected) == matches,
        "display_order_equal": actual == expected,
    }


def main() -> None:
    fixture = json.loads(Path(__file__).with_name("loc_expected.json").read_text())
    request = Request(fixture["source_url"], headers={"User-Agent": "film-iq-research/0.1"})
    started = perf_counter()
    try:
        with urlopen(request, timeout=20) as response:
            result = evaluate(response.read(), fixture["titles"], fixture["document_sha256"])
            result.update(
                status=response.status,
                cache_age_seconds=response.headers.get("Age"),
                checked_at=datetime.now(UTC).isoformat(),
            )
    except (URLError, ValueError) as error:
        raise SystemExit(f"Source check could not complete; result is unknown: {error}") from error
    result["elapsed_seconds"] = round(perf_counter() - started, 3)
    print(json.dumps(result, sort_keys=True))
    if not result["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
