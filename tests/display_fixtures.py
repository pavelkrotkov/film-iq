"""Synthetic reviewed display metadata; no publisher content or private ratings."""

import json
from datetime import UTC, datetime, timedelta

NOW = datetime(2026, 10, 31, tzinfo=UTC)


def payload():
    return {
        "version": "reviewed-display-v1",
        "observed_at": (NOW - timedelta(days=1)).isoformat(),
        "expires_at": (NOW + timedelta(days=5)).isoformat(),
        "attribution": "Synthetic reviewed metadata",
        "records": [
            {
                "tmdb_id": 123,
                "title": "Reviewed English title",
                "original_title": "Original title",
                "directors": ["Reviewed director"],
                "release_date": "2025-01-29",
                "runtime_minutes": 105,
                "reviewer": "synthetic-reviewer",
                "evidence": ["https://example.test/movie/123"],
            }
        ],
    }


def catalog_path(tmp_path, data=None):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(payload() if data is None else data))
    return path
