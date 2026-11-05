"""Verify coverage counts, identity errors and rate-limit stopping with fixtures."""

from tmdb_coverage import coverage
from tmdb_readonly import TMDbRateLimited


def main() -> None:
    films = [
        {"tmdb_id": 11, "title": "Fictional A"},
        {"tmdb_id": 12, "title": "Fictional B"},
        {"tmdb_id": 13, "title": "Fictional C"},
    ]
    calls = []

    def get(path, _parameters):
        calls.append(path)
        if path.endswith("12"):
            raise TMDbRateLimited("TMDB returned HTTP 429")
        return {
            "id": 11,
            "title": "Fictional alternative",
            "original_title": "FICTIONAL A",
            "overview": "Fictional synopsis",
            "release_date": "2001-01-01",
            "poster_path": "/fictional.jpg",
            "genres": [{"name": "Fiction"}],
            "credits": {"crew": [{"job": "Director", "name": "Fictional Director"}]},
        }

    result = coverage(films, get, lambda _: None)
    assert len(calls) == 2 and result["stopped_on_access_or_rate_limit"] is True
    assert result["counts"]["title_exact_normalized"] == 0
    assert result["counts"]["additional_original_title_matches"] == 1
    assert result["counts"]["director"] == 1 and result["counts"]["failed"] == 1
    try:
        coverage([films[0], films[0]], get, lambda _: None)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate IDs must fail before requesting metadata")
    print("Synthetic TMDB coverage and rate-limit checks passed")


if __name__ == "__main__":
    main()
