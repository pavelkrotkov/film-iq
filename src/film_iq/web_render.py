"""Responsive, native-HTML discovery pages with visible source and freshness context."""

from datetime import UTC, datetime

from film_iq.web_data import KIND_LABELS, WATCHED, kinds, watched_label
from film_iq.web_evidence import credits
from film_iq.web_html import film_meta, link, text, title


def layout(heading: str, body: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{text(heading)} · FilmIQ</title><link rel="stylesheet" href="/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header class="masthead">
<a class="brand" href="/">Film<span>IQ</span><small>A considered watch.</small></a>
<nav aria-label="Main"><a href="/">Discover</a></nav>
<span class="private">Your private film notebook</span></header>
<main id="main">{body}</main><footer>Follow the evidence. Keep your own taste.</footer></body></html>"""


def freshness(report: dict) -> str:
    state = (
        "History unavailable or stale — watched status is unknown."
        if report["personal_state_stale"]
        else "History refreshed successfully."
    )
    refreshed = report["last_successful_refresh"]
    when = (
        datetime.fromisoformat(refreshed).astimezone(UTC).strftime("%b %d, %Y · %H:%M UTC")
        if refreshed
        else "not yet synced"
    )
    return f'<aside class="notice">{state} <span>Last successful sync: {text(when)}</span></aside>'


def controls(values: dict[str, str]) -> str:
    return f'''<form class="filters" method="get" role="search">
<label class="search">Find a film or director<input type="search" name="q" value="{text(values["q"])}" placeholder="A title, a director, a new direction…"></label>
{dropdown("kind", "Recognition", {"all": "All evidence", **KIND_LABELS}, values["kind"])}
{dropdown("watched", "Watch history", WATCHED, values["watched"])}
{dropdown("order", "Order", {"public-support": "Public support", "source": "Source order"}, values["order"])}
<button type="submit">Find films</button></form>'''


def dropdown(name: str, label: str, choices: dict[str, str], selected: str) -> str:
    options = "".join(
        f'<option value="{text(value)}"{" selected" if value == selected else ""}>{text(caption)}</option>'
        for value, caption in choices.items()
    )
    return f'<label>{text(label)}<select name="{text(name)}">{options}</select></label>'


def card(item: dict, index: int) -> str:
    reasons = item["source_reasons"]
    tags = "".join(
        f'<span class="tag">{text(KIND_LABELS[kind])}</span>'
        for kind in KIND_LABELS
        if kind in kinds(item)
    )
    first = reasons[0]
    reason = link(first["source_url"], first["ballot_scope"])
    return f"""<article class="film-card"><span class="card-number">{index:02}</span>
<div class="tags">{tags}</div><h2><a href="/films/{item["tmdb_id"]}">{text(title(item))}</a></h2>
<p class="film-meta">{film_meta(item) or "Film details not supplied"}</p>
<p class="source">{reason}</p><p class="card-note">{len(reasons)} source selection(s) · {text(watched_label(item))}</p>
<a class="details-link" href="/films/{item["tmdb_id"]}">Explore the evidence <span aria-hidden="true">→</span></a></article>"""


def browse(report: dict, items: list[dict], values: dict[str, str], total: int) -> str:
    cards = "".join(card(item, index) for index, item in enumerate(items, 1))
    empty = '<section class="empty"><h2>No films match these filters</h2><p>Try another title or choose all evidence and all films.</p><a href="/">Reset filters</a></section>'
    ordering = (
        "Source selection order."
        if values["order"] == "source"
        else "More independent evidence groups appear first; ties retain source order. This provisional public-recognition order keeps your personal taste separate. Unknown support stays unscored."
    )
    count = f"{len(items)} {'film' if len(items) == 1 else 'films'} to explore"
    body = f"""<section class="intro"><p class="eyebrow">THE DISCOVERY NOTEBOOK</p>
<h1>Good films.<br><em>Reasons to care.</em></h1><p>Cinema selected by critics, festivals and archives.<br>Explore what brought each film here — and follow it to the source.</p></section>
{freshness(report)}{controls(values)}<div class="results-heading"><h2>{count}</h2><span>{total} accepted films in your selected sources</span></div>
<p class="ordering">{text(ordering)}</p>
<div class="film-grid">{cards}</div>{empty if not items else ""}
<p class="muted">{report["unresolved"]} source entries have unresolved film identities and are excluded from these cards. Source coverage is intentionally bounded, not a complete cinema catalog.</p>{credits(report)}"""
    return layout("Discover", body)
