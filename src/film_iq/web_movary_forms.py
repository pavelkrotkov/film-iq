"""Deliberate personal actions; credentials and private comments never enter HTML."""

from film_iq.web_html import text, title
from film_iq.web_movary_links import native_editor
from film_iq.web_render import layout


def hidden(name: str, value: str) -> str:
    return f'<input type="hidden" name="{text(name)}" value="{text(value)}">'


def form(item: dict, action: str, fields: str, caption: str, csrf: str) -> str:
    return f'<form method="post" action="/films/{item["tmdb_id"]}/movary/{action}">{hidden("csrf_token", csrf)}{fields}<button type="submit">{text(caption)}</button></form>'


def panel(item: dict, snapshot, settings, enabled: bool, csrf: str) -> str:
    body = native_editor(item, snapshot, settings)
    if not enabled:
        return (
            body
            + '<p class="muted">Movary actions are unavailable until the server has its API and complete-export configuration. You can keep browsing.</p>'
        )
    body += form(item, "watchlist/preview", "", "Preview watchlist addition", csrf)
    day = '<label>Watch date <input type="date" name="date" required></label>'
    body += form(item, "watched/preview", day, "Preview watch date", csrf)
    body += form(item, "refresh", "", "Refresh history and ratings", csrf)
    return '<section class="detail-section"><h2>Keep track in Movary</h2>' + body + "</section>"


def confirmation(item: dict, action: str, day: str, signature: str, csrf: str) -> str:
    target = f"{title(item)} (TMDB {item['tmdb_id']})"
    if action == "watchlist":
        description = f"Add {target} to your intentional Movary watchlist."
    else:
        description = f"Log a watch of {target} on {day}. Existing dates, plays, ratings and comments remain. Movary may remove this film from your watchlist according to your settings."
    fields = hidden("date", day) + hidden("signature", signature)
    approve = form(item, f"{action}/confirm", fields, "Confirm this Movary change", csrf)
    body = f'<section class="empty"><h1>Preview Movary change</h1><p>{text(description)}</p><p>No Movary request has been made. Confirm only if this is the film and action you intend.</p>{approve}<a href="/films/{item["tmdb_id"]}">Cancel</a></section>'
    return layout("Confirm Movary action", body)


def notice(item: dict, message: str) -> str:
    return layout(
        "Movary action",
        f'<section class="empty"><h1>Movary action</h1><p>{text(message)}</p><a href="/films/{item["tmdb_id"]}">Return to the film</a></section>',
    )
