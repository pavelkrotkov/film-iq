import io
import json
import os
import subprocess
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from film_iq.movary import MovaryClient, export_ratings, read_ratings

FIXTURE = Path(__file__).parent / "fixtures" / "movary-ratings.csv"


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
    with (
        patch(
            "film_iq.movary.urlopen",
            return_value=response({"played": [], "currentPage": 1, "maxPage": 2}),
        ),
        pytest.raises(ValueError),
    ):
        client.read("played")


def test_snapshot_replacement_and_failures(tmp_path):
    snapshot = tmp_path / "ratings.csv"
    fixture = FIXTURE.read_text()

    def run(command, **kwargs):
        Path(command[-1]).write_text(fixture)

    with patch("film_iq.movary.subprocess.run", side_effect=run):
        assert len(export_ratings(["movary", "user:export:ratings", "1"], snapshot)) == 2
        assert export_ratings(["movary"], snapshot) == read_ratings(snapshot)
        fixture = "title,year,tmdbId,imdbId,userRating\nRated Only,2002,200,tt0000200,10\n"
        assert len(export_ratings(["movary"], snapshot)) == 1
        assert read_ratings(snapshot)[0]["tmdbId"] == "200"
        fixture = "title,year,tmdbId,imdbId,userRating\nBroken\n"
        with pytest.raises(ValueError):
            export_ratings(["movary"], snapshot)
    before = snapshot.read_bytes()
    with (
        patch(
            "film_iq.movary.subprocess.run", side_effect=subprocess.CalledProcessError(1, "movary")
        ),
        pytest.raises(subprocess.CalledProcessError),
    ):
        export_ratings(["movary"], snapshot)
    assert snapshot.read_bytes() == before


@pytest.mark.skipif(not os.getenv("MOVARY_INTEGRATION"), reason="opt-in live Movary read")
def test_live_movary():
    client = MovaryClient(
        os.environ["MOVARY_URL"], os.environ["MOVARY_USERNAME"], os.environ["MOVARY_TOKEN"]
    )
    for collection in ("played", "history", "watchlist"):
        assert isinstance(client.read(collection), list)
    assert isinstance(read_ratings(Path(os.environ["MOVARY_RATINGS_CSV"])), list)
