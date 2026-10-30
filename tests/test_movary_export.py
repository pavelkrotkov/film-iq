import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from film_iq.movary import export_ratings, read_ratings

FIXTURE = Path(__file__).parent / "fixtures" / "movary-ratings.csv"


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
