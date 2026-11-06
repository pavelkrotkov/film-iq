"""Deterministic check for the credential-free TMDB response adapter."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

from tmdb_readonly import (
    TMDbAccessDenied,
    TMDbError,
    TMDbRateLimited,
    configured_reader,
    configured_refresh_enabled,
    fetch,
    paced_getter,
    read_movie,
)


def fixture(path, parameters=None):
    if path == "movie/42":
        return {
            "id": 42,
            "title": "Synthetic film",
            "original_title": "Fictional original title",
            "overview": "Synthetic synopsis.",
            "release_date": "2001-02-03",
            "genres": [{"name": "Drama"}],
            "poster_path": "/fixture.jpg",
            "credits": {"crew": [{"job": "Director", "name": "Synthetic director"}]},
            "external_ids": {"id": 42, "imdb_id": "tt0000042"},
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
    assert movie.original_title == "Fictional original title"
    assert movie.imdb_title_url == "https://www.imdb.com/title/tt0000042/"
    for invalid_original in (None, "  ", 42, ["Fictional original title"]):

        def invalid_original_fixture(path, parameters=None, *, value=invalid_original):
            result = fixture(path, parameters)
            if path == "movie/42":
                result["original_title"] = value
            return result

        assert read_movie(42, invalid_original_fixture, now).original_title is None
    for external in (
        {"imdb_id": "tt0000042/../../unsafe"},
        {"id": 43, "imdb_id": "tt0000042"},
        None,
    ):

        def external_fixture(path, parameters=None, *, external=external):
            result = fixture(path, parameters)
            if path == "movie/42":
                assert parameters == {"append_to_response": "credits,external_ids"}
                result["external_ids"] = external
            return result

        assert read_movie(42, external_fixture, now).imdb_title_url is None
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
    with (
        patch.dict("os.environ", {"TMDB_READ_ACCESS_TOKEN": "synthetic"}),
        patch("urllib.request.build_opener") as opener,
    ):
        opener.return_value.open.side_effect = HTTPError(
            "https://example.invalid/?secret", 429, "rate limit", Message(), None
        )
        try:
            fetch("movie/42")
        except TMDbRateLimited as error:
            assert str(error) == "TMDB returned HTTP 429"
        else:
            raise AssertionError("HTTP 429 was not recognized")
    for limited_path in ("movie/42", "configuration", "movie/42/watch/providers"):
        calls = []

        def limited(path, parameters=None, *, calls=calls, limited_path=limited_path):
            calls.append(path)
            if path == limited_path:
                raise TMDbRateLimited("fixture")
            return fixture(path, parameters)

        try:
            read_movie(42, limited, now)
        except TMDbRateLimited:
            assert calls[-1] == limited_path
        else:
            raise AssertionError("rate limit was swallowed")
    with (
        patch.dict("os.environ", {"TMDB_READ_ACCESS_TOKEN": "synthetic"}),
        patch("urllib.request.build_opener") as opener,
    ):
        for status in (401, 403):
            opener.return_value.open.side_effect = HTTPError(
                "https://example.invalid/?secret", status, "denied", Message(), None
            )
            try:
                fetch("movie/42")
            except TMDbAccessDenied as error:
                assert str(error) == "TMDB authorization denied"
            else:
                raise AssertionError("Access denial was not recognized")
    for denied_path in ("movie/42", "configuration", "movie/42/watch/providers"):
        calls = []

        def denied(path, parameters=None, *, denied_path=denied_path, calls=calls):
            calls.append(path)
            if path == denied_path:
                raise TMDbAccessDenied("fixture")
            return fixture(path, parameters)

        try:
            read_movie(42, denied, now)
        except TMDbAccessDenied:
            assert calls[-1] == denied_path
        else:
            raise AssertionError("Access denial was swallowed")
    for failing_path in ("movie/42", "configuration", "movie/42/watch/providers"):
        calls = []

        def failing(path, parameters=None, *, failing_path=failing_path, calls=calls):
            calls.append(path)
            if path == failing_path:
                raise TMDbError("fictional transport failure")
            return fixture(path, parameters)

        try:
            read_movie(42, failing, now, strict=True)
        except TMDbError:
            assert calls[-1] == failing_path
        else:
            raise AssertionError("Strict batch mode swallowed an upstream failure")

    tick = [0.0]
    starts, delays = [], []

    def clock():
        return tick[0]

    def sleep(delay):
        delays.append(delay)
        tick[0] += delay

    def fake_get(path, parameters=None):
        starts.append(clock())
        tick[0] += 0.25
        if path == "failure":
            raise TMDbError("fictional failure")
        return {}

    paced = paced_getter(fake_get, clock=clock, sleep=sleep)
    paced("first")
    try:
        paced("failure")
    except TMDbError:
        pass
    else:
        raise AssertionError("Paced provider failure was hidden")
    paced("third")
    assert starts == [0.0, 1.0, 2.0] and delays == [0.75, 0.75]
    tick[0] += 2
    paced("slow-gap")
    assert starts[-1] == 4.25 and delays == [0.75, 0.75]
    tick[0] = 0.0
    starts.clear()
    delays.clear()
    concurrent = paced_getter(fake_get, clock=clock, sleep=sleep)
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(concurrent, ("one", "two", "three")))
    assert starts == [0.0, 1.0, 2.0] and delays == [0.75, 0.75]
    assert configured_reader({}) is read_movie
    assert configured_reader({"FILMIQ_TMDB_PACE": "0"}) is read_movie
    assert configured_reader({"FILMIQ_TMDB_PACE": "1"}) is not read_movie
    with patch("tmdb_readonly.paced_getter", return_value=fixture) as factory:
        assert configured_reader({"FILMIQ_TMDB_PACE": "1"})(42).tmdb_id == 42
        factory.assert_called_once_with()
    for invalid in ("", "2", "true"):
        try:
            configured_reader({"FILMIQ_TMDB_PACE": invalid})
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid pace configuration was accepted")
    assert configured_refresh_enabled({}) is True
    assert configured_refresh_enabled({"FILMIQ_TMDB_REFRESH_ENABLED": "0"}) is False
    assert configured_refresh_enabled({"FILMIQ_TMDB_REFRESH_ENABLED": "1"}) is True
    for invalid in ("", "2", "true"):
        try:
            configured_refresh_enabled({"FILMIQ_TMDB_REFRESH_ENABLED": invalid})
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid refresh configuration was accepted")
    print("TMDB adapter parsed synthetic metadata and preserved unknown on provider failure")
