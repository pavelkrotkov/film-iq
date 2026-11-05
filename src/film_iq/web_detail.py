"""A film's reasons and original assertions stay visible beside optional personal state."""

from film_iq.web_data import watched_label
from film_iq.web_evidence import components, credits, source_reason
from film_iq.web_html import fields, film_meta, link, text, title
from film_iq.web_offers import viewing
from film_iq.web_render import freshness, layout


def personal(item: dict) -> str:
    merit = item["personal_artistic_merit"]
    if item["merit_status"] in {"conflict", "invalid"}:
        merit = "unknown — conflicting or invalid source entries"
    return fields(
        [
            ("Watch status", watched_label(item)),
            (
                "Recorded watch dates",
                ", ".join(str(day or "undated") for day in item["watched_dates"])
                or "none supplied",
            ),
            ("Your enjoyment /10", item["personal_enjoyment"]),
            ("Your artistic merit /10", merit),
        ]
    )


def display_context(item: dict) -> str:
    display = item.get("display")
    if not display:
        return '<p class="muted">No current reviewed display metadata supplied; headings use original source assertions.</p>'
    facts = fields(
        [
            ("Reviewed display title", display["title"]),
            ("Original-language title", display["original_title"]),
            ("Catalog release date", display["release_date"]),
            ("Review", display["reviewer"]),
        ]
    )
    evidence = " · ".join(link(url, "Display evidence") for url in display["evidence"])
    return f"<details><summary>Reviewed display facts</summary>{facts}<p>{evidence}</p><p>Catalog release dates do not rewrite source-listed years.</p></details>"


def detail(report: dict, item: dict) -> str:
    reasons = "".join(source_reason(reason) for reason in item["source_reasons"])
    body = f"""<a class="back" href="/">← Back to discovery</a>
<section class="film-heading"><p class="eyebrow">THE FILM NOTEBOOK</p><h1>{text(title(item))}</h1>
<p class="film-meta">{film_meta(item)}</p><p>{link(f"https://www.themoviedb.org/movie/{item['tmdb_id']}", f"Reviewed identity · TMDB {item['tmdb_id']}")}</p></section>
{freshness(report)}{display_context(item)}
<section class="detail-section"><p class="eyebrow">WHY IT IS HERE</p><h2>Follow the evidence</h2><div class="evidence-grid">{reasons}</div>{components(item)}</section>
<details><summary>Your film notes · optional</summary>{personal(item)}<p class="muted">Public recognition is separate from your own judgment.</p></details>
<section class="detail-section"><h2>Where to watch</h2>{viewing(item)}</section>{credits(report)}"""
    return layout(title(item), body)
