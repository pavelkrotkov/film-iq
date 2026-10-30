"""Explicit ID crosswalks; unresolved CSV rows never match by title."""

from collections import defaultdict


def api_movies(collections: dict[str, list[dict]]) -> dict[int, dict]:
    movies: dict[int, dict] = {}
    for name, rows in collections.items():
        for row in rows:
            movie = row["movie"]
            ids = movie["ids"]
            if type(ids["tmdb"]) is not int or type(ids["movary"]) is not int:
                raise ValueError("Invalid Movary/TMDB crosswalk")
            tmdb, movary = ids["tmdb"], ids["movary"]
            if min(tmdb, movary) < 1:
                raise ValueError("Invalid Movary/TMDB crosswalk")
            item = movies.setdefault(tmdb, {"movary_id": movary, "title": movie.get("title")})
            if item["movary_id"] != movary:
                raise ValueError("Conflicting Movary/TMDB crosswalk")
            item[name] = True
    return movies


def index(rows: list[dict[str, str]]) -> dict[int, list[dict[str, str]]]:
    result: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["tmdbId"]:
            result[int(row["tmdbId"])].append(row)
    return result
