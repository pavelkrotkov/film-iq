"""Unknown and conflicting IDs remain explicit rather than matched by title."""

import pytest
from test_personal_snapshot import api

from film_iq.personal_snapshot import build_snapshot


def test_unresolved_csv_retained_without_title_matching():
    ratings = [{"tmdbId": "", "title": "Synthetic", "userRating": "7"}]
    result = build_snapshot({"played": [api()]}, ratings, [])
    assert result["unresolved"]["ratings"] == ratings
    assert result["films"][0]["personal_enjoyment"] is None


def test_crosswalk_and_native_rating_conflicts_fail():
    with pytest.raises(ValueError, match="crosswalk"):
        build_snapshot({"played": [api(), api(10, 3)]}, [], [])
    ratings = [{"tmdbId": "10", "title": "Synthetic", "userRating": str(value)} for value in (7, 8)]
    with pytest.raises(ValueError, match="Conflicting enjoyment"):
        build_snapshot({}, ratings, [])
