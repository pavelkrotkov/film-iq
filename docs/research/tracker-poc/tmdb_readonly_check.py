"""Deterministic check for the credential-free TMDB response adapter."""

from datetime import UTC, datetime

from tmdb_readonly import TMDbError, read_movie


def fixture(path, parameters=None):
    if path == "movie/42":
        return {
            "id": 42,
            "title": "Synthetic film",
            "overview": "Synthetic synopsis.",
            "release_date": "2001-02-03",
            "genres": [{"name": "Drama"}],
            "poster_path": "/fixture.jpg",
            "credits": {"crew": [{"job": "Director", "name": "Synthetic director"}]},
        }
    if path == "configuration":
        return {
            "images": {"secure_base_url": "https://example.invalid/t/p/", "poster_sizes": ["w500"]}
        }
    if path == "movie/42/watch/providers":
        return {
            "id": 42,
            "results": {
                "US": {
                    "link": "https://example.invalid",
                    "flatrate": [{"provider_id": 1, "provider_name": "Fixture Stream"}],
                    "rent": [{"provider_id": 2, "provider_name": "Fixture Rental"}],
                }
            },
        }
    raise AssertionError(path)


def failed_providers(path, parameters=None):
    if path == "movie/42/watch/providers":
        raise TMDbError("simulated failure")
    return fixture(path, parameters)


def malformed_metadata(path, parameters=None):
    result = fixture(path, parameters)
    if path == "movie/42":
        result["release_date"] = "2001-invalid"
        result["genres"] = [{"name": "Drama"}, {}]
    return result


def wrong_identity(path, parameters=None):
    result = fixture(path, parameters)
    if path == "movie/42":
        result["id"] = 42.0
    return result


if __name__ == "__main__":
    now = datetime(2026, 11, 5, tzinfo=UTC)
    movie = read_movie(42, fixture, now)
    assert (movie.tmdb_id, movie.year, movie.genres, movie.directors) == (
        42,
        2001,
        ("Drama",),
        ("Synthetic director",),
    )
    assert movie.poster_url == "https://example.invalid/t/p/w500/fixture.jpg"
    assert {offer.kind for offer in movie.availability.offers} == {"subscription", "rent"}
    failed = read_movie(42, failed_providers, now)
    assert failed.availability.status == "unknown" and not failed.availability.offers
    malformed = read_movie(42, malformed_metadata, now)
    assert malformed.year is None and malformed.genres is None
    try:
        read_movie(42, wrong_identity, now)
    except TMDbError:
        pass
    else:
        raise AssertionError("invalid response identity was accepted")
    print("TMDB adapter parsed synthetic metadata and preserved unknown on provider failure")
