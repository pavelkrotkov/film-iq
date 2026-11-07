"""Deterministic checks for read-only reviewed-catalog display facts."""

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

from reviewed_catalog import catalog_facts


def main() -> None:
    path = Path("fictional-reviewed-catalog.json")
    now = datetime(2026, 1, 15, tzinfo=UTC)
    payload: dict[str, Any] = {
        "version": "reviewed-display-v1",
        "observed_at": "2026-01-01T00:00:00+00:00",
        "expires_at": "2026-01-30T00:00:00+00:00",
        "attribution": "Fictional catalog attribution",
        "records": [
            {
                "tmdb_id": 42,
                "title": "Fictional Film",
                "original_title": "Fictional Original",
                "directors": ["Fictional Director"],
                "release_date": "2001-02-03",
                "runtime_minutes": 100,
                "reviewer": "Private reviewer must not be returned",
                "evidence": ["Private evidence must not be returned"],
            }
        ],
    }

    def read(data, ident=42, title="fictional  film", at=now):
        with patch.object(Path, "read_text", return_value=json.dumps(data)):
            return catalog_facts(path, ident, title, at)

    result = read(payload)
    assert result == {
        "tmdb_id": 42,
        "title": "Fictional Film",
        "original_title": "Fictional Original",
        "year": 2001,
        "directors": ["Fictional Director"],
        "runtime_minutes": 100,
        "source": "Reviewed display catalog",
        "observed_at": "2026-01-01T00:00:00+00:00",
        "expires_at": "2026-01-30T00:00:00+00:00",
        "attribution": "Fictional catalog attribution",
    }
    assert read(payload, title="  FICTIONAL\tORIGINAL  ") == result
    assert read(payload, ident=43) is None
    assert read(payload, title="Different Film") is None
    assert read(payload, at=datetime(2026, 1, 30, tzinfo=UTC)) is None
    assert read(payload, at=datetime(2025, 12, 31, tzinfo=UTC)) is None
    assert read(payload, at=datetime(2026, 1, 15)) is None
    assert catalog_facts(None, 42, "Fictional Film", now) is None
    assert catalog_facts(path, True, "Fictional Film", now) is None
    assert catalog_facts(path, 42, " ", now) is None

    duplicate = deepcopy(payload)
    duplicate["records"].append(deepcopy(duplicate["records"][0]))
    assert read(duplicate) is None
    malformed = deepcopy(payload)
    malformed["records"][0]["directors"] = []
    assert read(malformed) is None
    oversized = deepcopy(payload)
    oversized["records"][0]["title"] = "x" * 513
    assert read(oversized, title="x" * 513) is None
    expired_window = deepcopy(payload)
    expired_window["expires_at"] = "2027-01-30T00:00:00+00:00"
    assert read(expired_window) is None
    with patch.object(Path, "read_text", side_effect=FileNotFoundError):
        assert catalog_facts(path, 42, "Fictional Film", now) is None
    with patch.object(Path, "read_text", return_value="not JSON"):
        assert catalog_facts(path, 42, "Fictional Film", now) is None
    print("Reviewed catalog identity, provenance, expiry and failure checks passed")


if __name__ == "__main__":
    main()
