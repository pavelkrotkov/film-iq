"""An offline, synthetic-only cache. No provider integration is present here."""

from datetime import UTC, datetime
from pathlib import Path

from tmdb_cache import initialize_authority, read_film, write_film

from film_iq.retention import CachePolicy

IDS = frozenset({900000001, 900000002})
POLICY = CachePolicy(
    "TMDB", True, "Fictional data only", "Fictional fixture", datetime(2027, 1, 1, tzinfo=UTC)
)


def seed(directory: Path, now: datetime) -> None:
    """Initialize only an empty fixture directory; never overwrite an existing cache."""
    root, authority = directory / "cache", directory / "authority.json"
    initialize_authority(root, authority, POLICY, now)
    for ident in IDS:
        write_film(
            root,
            POLICY,
            {
                "tmdb_id": ident,
                "title": "Fictional film" if ident == 900000001 else "Fictional film 2",
                "synopsis": "Synthetic source synopsis.",
                "year": 2001,
                "genres": ["Drama"],
                "directors": ["Fictional Director"],
                "availability": {
                    "status": "complete",
                    "checked_at": now.isoformat(),
                    "provider_url": None,
                    "offers": [
                        {"provider": "Fixture Stream", "kind": "subscription"},
                        {"provider": "Fixture Rental", "kind": "rent"},
                    ],
                },
            },
            now,
            now,
            authority=authority,
        )


def read(directory: Path, ident: int, now: datetime) -> dict | None:
    if type(ident) is not int or ident not in IDS:
        return None
    record = read_film(
        directory / "cache", POLICY, ident, now, authority=directory / "authority.json"
    )
    if not record or not record["metadata"]:
        return None
    metadata = dict(record["metadata"]["data"])
    metadata.pop("poster_path", None)
    metadata["poster_url"] = None
    availability = record["availability"]
    return {
        "tmdb_id": ident,
        **metadata,
        "availability": (
            {**availability["data"], "checked_at": availability["observed_at"]}
            if availability
            else {"status": "unknown", "checked_at": None, "offers": []}
        ),
    }
