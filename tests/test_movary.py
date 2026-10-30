"""Exercise Movary's advertised pagination using in-memory HTTP responses.

Only a final page may be short; an empty final page after a full page is an
incomplete snapshot. Page counts alone must never hide missing watched records.
"""

import io
import json
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from film_iq.movary import MovaryClient


def response(collection, movies, current=1, last=2):
    data = {collection: movies, "currentPage": current, "maxPage": last}
    return io.BytesIO(json.dumps(data).encode())


def read_pages(collection, *pages):
    """Serve only the supplied pages; an unexpected extra request fails the test."""
    with patch("film_iq.movary.urlopen", side_effect=pages):
        return MovaryClient("https://example.test", "user", "token").read(collection)


def test_api_pagination_and_failure():
    client = MovaryClient("https://example.test", "a user", "secret")
    movie = {"movie": {"ids": {"movary": 7, "tmdb": 42}}, "watchDates": [{"date": None}]}
    pages = [
        response("played", [movie] * 100),
        response("played", [movie], current=2),
    ]
    with patch("film_iq.movary.urlopen", side_effect=pages) as request:
        assert client.read("played") == [movie] * 101
        assert "/a%20user/played/movies?page=2&limit=100" in request.call_args.args[0].full_url
        assert request.call_args.args[0].get_header("Authorization") == "Bearer secret"
    for collection in ("history", "watchlist"):
        assert read_pages(collection, response(collection, [], last=0)) == []
    with (
        patch(
            "film_iq.movary.urlopen",
            side_effect=[
                response("played", [movie] * 100),
                HTTPError("x", 500, "error", Message(), None),
            ],
        ),
        pytest.raises(HTTPError),
    ):
        client.read("played")


@pytest.mark.parametrize("collection", ["played", "history", "watchlist"])
def test_empty_advertised_final_page(collection):
    pages = [
        response(collection, [{"movie": {}}] * 100),
        response(collection, [], current=2),
    ]
    with pytest.raises(ValueError):
        read_pages(collection, *pages)


def test_empty_single_page():
    assert read_pages("played", response("played", [], last=1)) == []
    with pytest.raises(ValueError):
        read_pages("played", response("played", []))


@pytest.mark.parametrize("collection", ["played", "history", "watchlist"])
@pytest.mark.parametrize("size,last", [(1, 2), (101, 2), (101, 1)])
def test_invalid_page_size(collection, size, last):
    pages = [
        response(collection, [{"movie": {}}] * size, last=last),
        response(collection, [{}], current=2),
    ]
    with pytest.raises(ValueError):
        read_pages(collection, *pages)


@pytest.mark.parametrize("collection", ["played", "history", "watchlist"])
def test_full_page_and_short_final_page(collection):
    movie = {"movie": {}}
    pages = [
        response(collection, [movie] * 100),
        response(collection, [movie], current=2),
    ]
    assert read_pages(collection, *pages) == [movie] * 101
