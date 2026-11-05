"""Human-readable original evidence, retaining rank, lineage and typed recognition."""

from film_iq.discovery_credits import CANONICAL, _inputs
from film_iq.recognition.render import LABELS, _fact
from film_iq.web_data import KIND_LABELS
from film_iq.web_html import fields, link, text


def source_reason(reason: dict) -> str:
    # Published ranks and ties are evidence; list position is not a rank fallback.
    rank = f"Rank #{reason['rank']}" if reason["rank"] is not None else "Unranked selection"
    tie = f" · tied ({reason['tie']})" if reason["tie"] else ""
    kind = KIND_LABELS[reason["evidence_kind"]]
    return f"""<article class="evidence"><p class="eyebrow">{text(kind)} · {text(rank + tie)}</p>
<h3>{link(reason["source_url"], reason["ballot_scope"])}</h3>
<p class="muted">Lineage: {text(reason.get("source_lineage_kind"))} · {text(reason.get("source_lineage"))}</p>
<details><summary>Original source record</summary>{fields([("Edition", reason["edition"]), ("Evidence type", kind), ("Source published", reason["published_at"]), ("Original film title", reason["raw_title"]), ("Source-listed year", reason["year"]), ("Source director", reason["director"]), ("Lineage kind", reason.get("source_lineage_kind")), ("Lineage", reason.get("source_lineage")), ("Completeness", reason.get("source_completeness")), ("Eligibility", reason.get("source_eligibility")), ("Source locator", reason["locator"])])}</details></article>"""


def components(item: dict) -> str:
    groups = item.get("public_evidence_components", {})
    body = "".join(
        component_group(kind, groups.get(kind, [])) for kind in LABELS if kind != "critic_selection"
    )
    missing = ", ".join(LABELS[kind] for kind in groups.get("missing", []))
    note = f"Evidence coverage unknown: {missing or 'additional sources'}. Missing evidence is not a negative judgment."
    return body + f'<p class="muted">{text(note)}</p>'


def component_group(kind: str, rows: list[dict]) -> str:
    if not rows:
        return ""
    facts = "".join(component(kind, row) for row in rows)
    return f'<h3>{text(LABELS[kind].capitalize())}</h3><div class="evidence-grid">{facts}</div>'


def component(kind: str, row: dict) -> str:
    # Reuse the report's recipient/category semantics instead of reinterpreting prizes.
    facts = "".join(f"<li>{text(_fact(kind, value))}</li>" for value in row["component"] or [])
    return f"""<article class="evidence"><ul>{facts}</ul><p>{link(row["url"], "Original source")}</p>
<details><summary>Original source record</summary>{fields([("Published", row["published_at"]), ("Edition", row["edition"]), ("Lineage", row["lineage"]), ("Lineage kind", row["lineage_kind"]), ("Original title", row["raw_title"]), ("Source-listed year", row["listed_year"])])}</details></article>"""


def credits(report: dict) -> str:
    # Arbitrary attribution is text; only the repository's fixed notice is HTML.
    sources, texts, watch_sources = _inputs(report)
    notices = [text(value) for value in sorted(texts)]
    if "tmdb" in sources:
        notices.append(CANONICAL["tmdb"])
    if "motn" in sources:
        notices.append(
            link(
                "https://www.movieofthenight.com/about/api",
                "Streaming Availability API by Movie of the Night",
            )
        )
    if "tmdb" in watch_sources:
        notices.append("Watch-provider data: " + link("https://www.justwatch.com/", "JustWatch"))
    return '<aside class="credits">' + "<br>".join(notices) + "</aside>" if notices else ""
