"""Record exact HTTP response bytes and retrieval receipts."""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

AGENT = "film-iq-research/0.1 (https://github.com/pavelkrotkov/film-iq; fixture audit)"


def fetch(parameters: dict[str, str], path: Path) -> tuple[dict, dict]:
    url = "https://en.wikipedia.org/w/api.php?" + urlencode(parameters | {"format": "json"})
    with urlopen(Request(url, headers={"User-Agent": AGENT}), timeout=30) as response:
        body = response.read()
        receipt = {
            "url": url,
            "response_url": response.url,
            "status": response.status,
            "accessed_at": datetime.now(UTC).isoformat(),
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "file": path.name,
        }
    data = json.loads(body)
    if "error" in data:
        raise ValueError(data["error"])
    path.write_bytes(body)
    time.sleep(0.7)
    return data, receipt
