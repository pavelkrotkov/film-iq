"""Synthetic source-to-watchlist integration seam."""

import pytest
from stub_backend import StubBackend

from film_iq.approval import Preview, sync_one


def test_mock_source_to_approved_watchlist() -> None:
    source = {"source_id": "poll", "entry_id": "entry-1", "raw_title": "Example", "rank": 1}
    identity = {"entry_id": source["entry_id"], "tmdb_id": 123}
    score = {"entry_id": identity["entry_id"], "significance": 1, "fit": None}
    offer = {"tmdb_id": identity["tmdb_id"], "region": "US", "kind": "free"}
    plan = {"title": source["raw_title"], "tmdb_id": offer["tmdb_id"], "score": score}
    preview = Preview(title=plan["title"], tmdb_id=plan["tmdb_id"])
    writer = StubBackend()

    with pytest.raises(PermissionError):
        sync_one(preview, writer, execute=True)
    with pytest.raises(PermissionError):
        sync_one(preview, writer, execute=True, approved=False)
    assert writer.writes == []
    assert plan["score"]["entry_id"] == source["entry_id"]
    assert (offer["region"], offer["kind"]) == ("US", "free")

    assert sync_one(preview, writer, execute=True, approved=True) == "added to watchlist"
    assert sync_one(preview, writer, execute=True, approved=True) == "already on watchlist"
    assert writer.writes == [("movie", 123), ("watchlist", 456)]
    assert writer.watchlist == {99, 456}


@pytest.mark.parametrize("title,tmdb_id", [("", 1), ("Example", 0), ("Example", True)])
def test_preview_rejects_invalid_identity(title: str, tmdb_id: int) -> None:
    with pytest.raises(ValueError):
        Preview(title, tmdb_id)
