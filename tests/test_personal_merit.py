"""Synthetic scores exercise explicit, nullable, date-entry merit semantics."""

import pytest

from film_iq.personal_merit import merit


def row(comment, watched="2026-01-01"):
    return {"comment": comment, "watchedAt": watched}


@pytest.mark.parametrize(
    "comments,expected",
    [
        (["Enjoyable"], (None, "unknown")),
        (["Artistic merit: 8/10", "Artistic merit: 9/10"], (None, "conflict")),
    ],
)
def test_explicit_merit(comments, expected):
    assert merit([row(comment) for comment in comments]) == expected
