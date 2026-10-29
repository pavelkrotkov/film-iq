import io
import json
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from film_iq.movary import MovaryClient


def response(data):
    return io.BytesIO(json.dumps(data).encode())


def test_api_pagination_and_failure():
    client = MovaryClient("https://example.test", "a user", "secret")
    movie = {"movie": {"ids": {"movary": 7, "tmdb": 42}}, "watchDates": [{"date": None}]}
    pages = [
        response({"played": [movie], "currentPage": 1, "maxPage": 2}),
        response({"played": [movie], "currentPage": 2, "maxPage": 2}),
    ]
    with patch("film_iq.movary.urlopen", side_effect=pages) as request:
        assert client.read("played") == [movie, movie]
        assert "/a%20user/played/movies?page=2&limit=100" in request.call_args.args[0].full_url
        assert request.call_args.args[0].get_header("Authorization") == "Bearer secret"
    for collection in ("history", "watchlist"):
        with patch(
            "film_iq.movary.urlopen",
            return_value=response({collection: [], "currentPage": 1, "maxPage": 0}),
        ):
            assert client.read(collection) == []
    with (
        patch(
            "film_iq.movary.urlopen",
            side_effect=[
                response({"played": [movie], "currentPage": 1, "maxPage": 2}),
                HTTPError("x", 500, "error", Message(), None),
            ],
        ),
        pytest.raises(HTTPError),
    ):
        client.read("played")


@pytest.mark.parametrize("collection", ["played", "history", "watchlist"])
def test_empty_advertised_final_page(collection):
    pages = [
        response({collection: [{"movie": {}}], "currentPage": 1, "maxPage": 2}),
        response({collection: [], "currentPage": 2, "maxPage": 2}),
    ]
    with patch("film_iq.movary.urlopen", side_effect=pages), pytest.raises(ValueError):
        MovaryClient("https://example.test", "user", "token").read(collection)


def test_empty_single_page():
    client = MovaryClient("https://example.test", "user", "token")
    with patch(
        "film_iq.movary.urlopen",
        return_value=response({"played": [], "currentPage": 1, "maxPage": 1}),
    ):
        assert client.read("played") == []
    with (
        patch(
            "film_iq.movary.urlopen",
            return_value=response({"played": [], "currentPage": 1, "maxPage": 2}),
        ),
        pytest.raises(ValueError),
    ):
        client.read("played")
