import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from film_iq.movary import MovaryClient, export_ratings


@pytest.mark.skipif(not os.getenv("MOVARY_INTEGRATION"), reason="opt-in live Movary read")
def test_live_movary():
    version = subprocess.run(
        json.loads(os.environ["MOVARY_VERSION_COMMAND"]),
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    assert version == os.environ["MOVARY_EXPECTED_VERSION"]
    client = MovaryClient(
        os.environ["MOVARY_URL"], os.environ["MOVARY_USERNAME"], os.environ["MOVARY_TOKEN"]
    )
    played = client.read("played")
    for collection in ("history", "watchlist"):
        client.read(collection)
    tmdb_id = os.environ["MOVARY_RATED_ONLY_TMDB_ID"]
    assert all(str(entry["movie"]["ids"]["tmdb"]) != tmdb_id for entry in played)
    with tempfile.TemporaryDirectory(dir=os.environ["MOVARY_SNAPSHOT_DIR"]) as directory:
        rows = export_ratings(
            json.loads(os.environ["MOVARY_EXPORT_COMMAND"]), Path(directory) / "ratings.csv"
        )
        assert any(row["tmdbId"] == tmdb_id for row in rows)
