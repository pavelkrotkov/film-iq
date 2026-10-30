"""No personal source data: deterministic synthetic Movary identities and scores."""

from film_iq.personal_snapshot import build_snapshot


def api(tmdb=10, movary=2):
    return {"movie": {"ids": {"tmdb": tmdb, "movary": movary}, "title": "Synthetic"}}


def test_both_scores_rated_only_unknown_date_and_crosswalk():
    collections = {"played": [api()], "history": [api()], "watchlist": [api(20, 3)]}
    ratings = [{"tmdbId": "20", "title": "Rated only", "userRating": "7"}]
    history = [
        {"tmdbId": "10", "title": "Synthetic", "watchedAt": "", "comment": "Artistic merit: 8/10"}
    ] * 2
    result = build_snapshot(collections, ratings, history)
    watched, rated = result["films"]
    assert watched["tmdb_id"] == 10 and watched["movary_id"] == 2
    assert watched["watched"] and watched["watched_dates"] == [None]
    assert watched["personal_artistic_merit"] == 8 and watched["personal_enjoyment"] is None
    assert not rated["watched"] and rated["watchlist"]
    assert rated["personal_enjoyment"] == 7 and rated["personal_artistic_merit"] is None
    assert result["provenance"]["history_csv"] == history
