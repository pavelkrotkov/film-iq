"""Fictional, network-free checks for the cache comparison."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import tmdb_cache_batch as batch
import tmdb_cache_compare as comparison


def film(ident, *, status="complete", provider="Fictional A", title="Fictional"):
    return {
        "tmdb_id": ident,
        "cache_expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "title": title,
        "genres": ["Drama", "Comedy"],
        "directors": ["Fictional Director"],
        "availability": {
            "status": status,
            "offers": [{"provider": provider, "kind": "subscription"}],
        },
    }


def main():
    allowed = {1, 2, 3, 4, 5, 6, 7}
    left = {
        1: film(1),
        2: film(2),
        3: film(3, status="unknown"),
        4: batch.CACHE_MISS,
        5: film(5, status="partial"),
        6: film(99),
        7: film(7),
    }
    right = {
        1: film(1),
        2: film(2, provider="Fictional B", title="Different fictional"),
        3: film(3),
        4: film(4),
        5: film(5, status="partial", provider="Fictional B"),
        6: film(6),
        7: film(7),
    }
    right[7]["cache_expires_at"] = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    # Reordered genre sets are equivalent.
    right[1]["genres"].reverse()
    report = {
        "validated": 0,
        "kaneo_missing": 0,
        "youtrack_missing": 0,
        "kaneo_invalid": 0,
        "youtrack_invalid": 0,
        "both_cached": 0,
        "both_valid": 0,
        "metadata_mismatches": 0,
        "availability_status_mismatches": 0,
        "provider_sets_compared": 0,
        "provider_sets_partial": 0,
        "provider_sets_unknown": 0,
        "provider_set_mismatches": 0,
    }

    def endpoint(_http, backend, record, *, refresh):
        assert refresh is False
        return (left if backend == "kaneo" else right)[record]

    mapping = {ident: ident for ident in allowed}
    with (
        patch.object(batch, "kaneo_records", return_value=mapping),
        patch.object(batch, "youtrack_records", return_value=mapping),
        patch.object(batch, "endpoint", side_effect=endpoint),
    ):
        comparison.compare(None, None, allowed, report)
    assert report == {
        "validated": 7,
        "kaneo_missing": 1,
        "youtrack_missing": 0,
        "kaneo_invalid": 1,
        "youtrack_invalid": 1,
        "both_cached": 6,
        "both_valid": 4,
        "metadata_mismatches": 1,
        "availability_status_mismatches": 1,
        "provider_sets_compared": 3,
        "provider_sets_partial": 1,
        "provider_sets_unknown": 1,
        "provider_set_mismatches": 2,
    }
    print("Fictional cache comparison and unknown-availability checks passed")


if __name__ == "__main__":
    main()
