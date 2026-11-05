"""Keep verified Movary writes distinct from the later disposable-cache refresh."""

from http.client import HTTPException
from subprocess import SubprocessError
from typing import cast

from film_iq.personal_io import private_json
from film_iq.personal_refresh import refresh
from film_iq.web_movary_api import MovieActions
from film_iq.web_movary_forms import notice
from film_iq.web_movary_rating import write_rating


def stale(snapshot) -> None:
    if snapshot:
        private_json(snapshot.with_suffix(snapshot.suffix + ".status"), {"stale": True})


def execute_result(
    item, action, day, settings, snapshot, exports, *, rating_command=None, rating=None
):
    result = ""
    try:
        api = MovieActions(item, settings)
        result = api.watchlist() if action == "watchlist" else api.watched(day)
        if rating is not None:
            write_rating(cast(list[str], rating_command), settings[1], item["tmdb_id"], rating)
            result += f" Enjoyment rating {rating}/10 saved in Movary."
    except (OSError, ValueError, KeyError, TypeError, HTTPException, SubprocessError):
        stale(snapshot)
        message = (
            (result + " " if result else "")
            + "Movary could not verify the complete change. It may have been saved; the FilmIQ cache is stale. Refresh before retrying."
        )
        return "502 Bad Gateway", notice(item, message), "text/html"
    return refresh_result(item, settings, snapshot, exports, result)


def refresh_result(item, settings, snapshot, exports, result=""):
    try:
        api = MovieActions(item, settings)
        refresh(api.client, snapshot, **exports)
    except (OSError, ValueError, KeyError, TypeError, HTTPException):
        stale(snapshot)
        message = (
            result + " " if result else ""
        ) + "FilmIQ refresh failed; the prior cache is stale."
        return "502 Bad Gateway", notice(item, message), "text/html"
    return "200 OK", notice(item, result + " History and ratings refreshed."), "text/html"
