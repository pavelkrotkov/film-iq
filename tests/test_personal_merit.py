"""Synthetic scores exercise explicit, nullable, date-entry merit semantics."""

import pytest

from film_iq.history_csv import read_history
from film_iq.personal_merit import merit


def row(comment, watched="2026-01-01"):
    return {"comment": comment, "watchedAt": watched}


@pytest.mark.parametrize(
    "comments,expected",
    [
        (["Enjoyable"], (None, "unknown")),
        (["Artistic merit: 8/10"], (8, "known")),
        (["Artistic merit: 8/10"] * 3, (8, "known")),
        (["Artistic merit: 8/10", "Artistic merit: 9/10"], (None, "conflict")),
        (["Artistic merit: 0/10"], (None, "invalid")),
        (["Artistic merit: 11/10"], (None, "invalid")),
        (["Artistic merit: 8/100"], (None, "invalid")),
        (["Artistic merit: 8/10 and Artistic merit: 12/10"], (None, "invalid")),
        (["Artistic merit: 10/10. Other private text"], (10, "known")),
    ],
)
def test_explicit_merit(comments, expected):
    assert merit([row(comment) for comment in comments]) == expected


def test_distinct_dates_and_deleted_tag():
    assert merit([row("Artistic merit: 8/10"), row("Artistic merit: 6/10", "2026-01-02")]) == (
        None,
        "conflict",
    )
    assert merit([row("Edited comment")]) == (None, "unknown")


@pytest.mark.parametrize(
    "tail", ["Bad\n", "Film,2000,0,,2026-01-01,,\n", "Film,2000,2,,invalid,,\n"]
)
def test_history_rejects_incomplete_schema(tmp_path, tail):
    path = tmp_path / "history.csv"
    path.write_text("title,year,tmdbId,imdbId,watchedAt,comment,location\n" + tail)
    with pytest.raises(ValueError):
        read_history(path)
