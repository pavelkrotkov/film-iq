"""A visible optional-rating form, using native calendar and score controls."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from film_iq.web_movary_forms import form


def rate_form(item: dict, csrf: str, rating_enabled: bool) -> str:
    options = '<option value="">Keep existing rating / unrated</option>' + "".join(
        f'<option value="{score}">{score}/10</option>' for score in range(1, 11)
    )
    rating = (
        f'<label>Enjoyment rating <select name="rating">{options}</select></label>'
        if rating_enabled
        else "<p>Rating entry is unavailable here; you can still mark this film watched.</p>"
    )
    today = datetime.now(ZoneInfo(os.environ.get("TZ", "America/New_York"))).date().isoformat()
    fields = (
        rating
        + f'<label>Watch date <input type="date" name="date" value="{today}" required></label>'
    )
    return (
        '<section id="rate-watched" class="rate-watched"><h2>Rate &amp; mark watched</h2>'
        "<p>A rating is optional. Leaving it blank keeps your current rating.</p>"
        + form(item, "rated-watched/preview", fields, "Review & save", csrf)
        + "</section>"
    )
