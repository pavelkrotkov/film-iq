"""One private replacement point for complete reads; failures preserve success."""

from unittest.mock import Mock

from film_iq.personal_refresh import refresh

HEADER = "title,year,tmdbId,imdbId,watchedAt,comment,location\n"
RATINGS = "title,year,tmdbId,imdbId,userRating\n"


def inputs(tmp_path):
    rated, history = tmp_path / "ratings.csv", tmp_path / "history.csv"
    rated.write_text(RATINGS + "Synthetic,2000,20,,7\n")
    history.write_text(HEADER + "Synthetic,2000,10,,2026-01-01,Artistic merit: 8/10,\n")
    return {"ratings_csv": rated, "history_csv": history}


def test_atomic_refresh_reconciles_deletions_and_private_permissions(tmp_path):
    paths = inputs(tmp_path)
    client, snapshot = Mock(), tmp_path / "snapshot.json"
    client.read.return_value = []
    first = refresh(client, snapshot, **paths)
    assert first["films"][1]["personal_enjoyment"] == 7
    assert first["films"][0]["personal_artistic_merit"] == 8
    assert snapshot.stat().st_mode & 0o777 == 0o600
    paths["ratings_csv"].write_text(RATINGS)
    paths["history_csv"].write_text(HEADER + "Synthetic,2000,10,,2026-01-01,edited,\n")
    second = refresh(client, snapshot, **paths)
    assert len(second["films"]) == 1
    assert second["films"][0]["personal_artistic_merit"] is None
    assert client.read.call_count == 6
