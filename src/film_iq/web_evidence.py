"""Human-readable original evidence, retaining rank, lineage and typed recognition."""

from film_iq.discovery_credits import CANONICAL, _inputs
from film_iq.recognition.render import LABELS, _fact
from film_iq.web_data import KIND_LABELS
from film_iq.web_html import fields, link, text


def source_reason(reason: dict, annotation: dict | None = None) -> str:
    # Published ranks and ties are evidence; list position is not a rank fallback.
    rank = f"Rank #{reason['rank']}" if reason["rank"] is not None else "Unranked selection"
    tie = f" · tied ({reason['tie']})" if reason["tie"] else ""
    kind = KIND_LABELS[reason["evidence_kind"]]
    reviewed = annotation["classification_reviewed"] if annotation else None
    facts = typed_facts(annotation) if annotation else ""
    return f"""<article class="evidence"><p class="eyebrow">{text(kind)} · {text(rank + tie)}</p>
<h3>{link(reason["source_url"], reason["ballot_scope"])}</h3>{facts}
<p class="muted">Lineage: {text(reason.get("source_lineage_kind"))} · {text(reason.get("source_lineage"))}</p>
<details><summary>Original source record</summary>{fields([("Edition", reason["edition"]), ("Evidence type", kind), ("Source published", reason["published_at"]), ("Original film title", reason["raw_title"]), ("Source-listed year", reason["year"]), ("Source director", reason["director"]), ("Lineage kind", reason.get("source_lineage_kind")), ("Lineage", reason.get("source_lineage")), ("Completeness", reason.get("source_completeness")), ("Eligibility", reason.get("source_eligibility")), ("Source locator", reason["locator"]), ("Extraction status", "accepted"), ("Classification reviewed", reviewed)])}</details></article>"""


def annotations(item: dict) -> dict[tuple, dict]:
    return {
        (row["entry_id"], row["revision_id"]): row
        for kind in (*LABELS, "unclassified")
        for row in item.get("public_evidence_components", {}).get(kind, [])
    }


def selected_evidence(item: dict) -> str:
    by_entry = annotations(item)
    return "".join(
        source_reason(reason, by_entry.get((reason["entry_id"], reason["revision_id"])))
        for reason in item["source_reasons"]
    )


def components(item: dict) -> str:
    groups = item.get("public_evidence_components", {})
    selected = {(reason["entry_id"], reason["revision_id"]) for reason in item["source_reasons"]}
    body = "".join(
        component_group(
            kind,
            [
                row
                for row in groups.get(kind, [])
                if (row["entry_id"], row["revision_id"]) not in selected
            ],
        )
        for kind in (*LABELS, "unclassified")
    )
    missing = ", ".join(LABELS[kind] for kind in groups.get("missing", []))
    note = f"Evidence coverage unknown: {missing or 'additional sources'}. Missing evidence is not a negative judgment."
    return body + f'<p class="muted">{text(note)}</p>'


def component_group(kind: str, rows: list[dict]) -> str:
    if not rows:
        return ""
    facts = "".join(component(row) for row in rows)
    label = LABELS.get(kind, "Unclassified sources").capitalize()
    return f'<h3>{text(label)}</h3><div class="evidence-grid">{facts}</div>'


def typed_facts(row: dict) -> str:
    # A performance prize stays attached to its person/category, not Best Film.
    if row["kind"] in {"critic_selection", "unknown"}:
        return ""
    facts = "".join(
        f"<li>{text(_fact(row['kind'], value))}</li>" for value in row["component"] or []
    )
    return f"<ul>{facts}</ul>" if facts else ""


def component(row: dict) -> str:
    reason = {
        "source_url": row["url"],
        "ballot_scope": row["author"] or row["source_id"],
        "edition": row["edition"],
        "evidence_kind": row["kind"],
        "published_at": row["published_at"],
        "raw_title": row["raw_title"],
        "year": row["listed_year"],
        "director": row["director"],
        "rank": row["rank"],
        "tie": row["tie"],
        "locator": row["locator"],
        "source_lineage_kind": row["lineage_kind"],
        "source_lineage": row["lineage"],
        "source_completeness": row["completeness"],
        "source_eligibility": row["eligibility"],
    }
    return source_reason(reason, row)


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
