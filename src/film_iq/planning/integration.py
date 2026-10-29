"""Provisional, public-evidence-only bridge from scoring to the planner."""

import sqlite3

from film_iq.planning.models import Film
from film_iq.scoring import VERSION, Score

UTILITY_VERSION = "independent-count-additive-v1"


def planner_film(
    db: sqlite3.Connection, score: Score, title: str, minutes: int, watched: bool
) -> Film:
    """Use the stored TMDB crosswalk and one utility point per independent endorsement.

    This policy is uncalibrated; it ignores rank and personal preference. Missing
    crosswalks fail instead of treating an internal ID as a TMDB ID.
    """
    if score.version != VERSION or score.independent_count <= 0:
        raise ValueError("A supported score with independent evidence is required")
    row = db.execute("SELECT tmdb_id FROM film_index WHERE id = ?", (score.film_id,)).fetchone()
    if row is None or type(row[0]) is not int or row[0] <= 0:
        raise ValueError("A valid TMDB crosswalk is required")
    return Film(
        row[0],
        title,
        minutes,
        float(score.independent_count),
        watched,
        f"{UTILITY_VERSION}: provisional, uncalibrated utility; one point per independent "
        "endorsement; rank and personal preference are ignored",
    )
