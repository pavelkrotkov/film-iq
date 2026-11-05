"""Native shortlist controls and scoped navigation for accepted film cards."""

from collections import Counter

from film_iq.dispositions import STATES, change
from film_iq.web_html import text

PATHS = {"discover": "/", "saved": "/saved", "dismissed": "/dismissed"}
VIEWS = {path: state for state, path in PATHS.items()}


def navigation(items: list[dict], view: str) -> str:
    counts = Counter(item["disposition"] for item in items)
    return "".join(
        f'<a href="{PATHS[state]}" aria-current="{"page" if state == view else "false"}">{label} <small>{counts[state]}</small></a>'
        for state, label in STATES.items()
    )


def actions(item: dict, csrf_token: str) -> str:
    state = item["disposition"]
    choices = {"saved": "Save", "dismissed": "Dismiss", "discover": "Restore to discovery"}
    buttons = "".join(
        f'<button class="secondary" name="state" value="{value}">{label}</button>'
        for value, label in choices.items()
        if value != state
    )
    return f'''<section class="local-actions" aria-label="FilmIQ recommendation controls"><p>FilmIQ shortlist · {STATES[state]}</p>
<form class="film-actions" method="post" action="/films/{item["tmdb_id"]}/disposition">
<input type="hidden" name="csrf_token" value="{text(csrf_token)}">{buttons}</form>
<a class="rate-link" href="/films/{item["tmdb_id"]}#rate-watched">Rate &amp; mark watched</a></section>'''


def submit(database, item, values):
    try:
        change(database, item["tmdb_id"], values.get("state", ""))
    except ValueError:
        return "400 Bad Request", "Unknown recommendation action.", "text/plain"
    return "303 See Other", f"/films/{item['tmdb_id']}", "text/plain"
