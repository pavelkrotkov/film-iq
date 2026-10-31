"""Human-readable discovery shortlist; technical evidence stays in a separate section."""

from film_iq.discovery_cards import card, personal, source_reason, text, title
from film_iq.discovery_order import public_support
from film_iq.discovery_selection import remaining
from film_iq.recognition.discovery import audit_components


def _audit(report):
    lines = [
        "<details>",
        "<summary>Source evidence and report details</summary>",
        "",
        f"{report['total_candidates']} source entries; {report['accepted']} accepted; {report['unresolved']} unresolved identities; {report['watched_excluded']} watched entries excluded from suggestions.",
        f"Personal history last refreshed: {text(report['last_successful_refresh'])}.",
        f"Declared selection scope: {report['completeness']}. Declared lineage: {report['lineage']}",
    ]
    lines.extend(["", report.get("ordering", {}).get("explanation", ""), *_catalog_status(report)])
    lines.extend(
        f"- {text(item['raw_title'])} — source director {text(item['director'])}, source year {text(item['year'])}: {source_reason(item)}; locator {text(item['locator'])}; published {text(item['published_at'])}; eligibility date {text(item['eligibility_date'])}; source completeness {text(item['source_completeness'])}; lineage {text(item['source_lineage_kind'])}: {text(item['source_lineage'])}; eligibility {text(item['source_eligibility'])}; edition {text(item['edition'])}; tie {text(item['tie'])}; reviewed evidence groups {text(public_support(item))}; catalog {text(item.get('display'))}."
        for item in report["candidates"]
    )
    lines.extend(audit_components(report["candidates"]))
    lines.extend(
        [
            "",
            f"Reviewed catalog release cohorts: {report.get('release_cohorts', 'not supplied')}",
            "</details>",
        ]
    )
    return lines


def markdown(report: dict) -> str:
    lines = [
        "# Your film shortlist",
        "",
        "Open a film title for details.",
    ]
    if report["personal_state_stale"]:
        lines.extend(
            [
                "",
                "Refresh your Movary history before choosing unwatched films; personal state is stale or unknown.",
            ]
        )
    lines.extend(
        [
            "",
            "Published selections below explain why each film is here.",
            "",
            "## Suggested next",
        ]
    )
    if "ordering" in report:
        lines.extend(
            [
                "Sorted by published source support; ties keep list order."
                if report["ordering"]["policy"] == "public-support"
                else "Shown in source list order.",
                "",
            ]
        )
    if not report["suggested_unwatched"]:
        lines.append(
            "No verified unwatched picks are ready yet. Source selections and review items are below."
        )
    for item in report["suggested_unwatched"]:
        lines.extend(["", *card(item)])
    lines.extend(
        [
            "",
            "## Viewing choices",
            "",
            *report["options"],
            "Rental and streaming availability, price and plan entitlement have not been verified. Your scores appear only where available.",
        ]
    )
    lines.extend(_other(remaining(report)))
    lines.extend(["", *_audit(report)])
    return "\n".join(lines) + "\n"


def _other(items):
    lines = ["", "## Other source selections and your history"]
    for item in items:
        if item["watched"] is True:
            lines.extend(["", f"- Already watched: {title(item)}. {personal(item)}"])
        else:
            lines.extend(["", *card(item)])
    return lines


def _catalog_status(report):
    context = report.get("display_catalog", {"status": "not_supplied"})
    if context["status"] != "fresh":
        return [f"Reviewed catalog display: {context['status']}; original source facts are shown."]
    return [
        f"Catalog facts checked {context['observed_at']}; expire {context['expires_at']}. {context['attribution']}"
    ]
