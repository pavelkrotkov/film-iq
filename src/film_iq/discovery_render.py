"""Human-readable discovery shortlist; technical evidence stays in a separate section."""

from film_iq.discovery_cards import card, personal, source_reason, text, title
from film_iq.discovery_selection import remaining


def _audit(report):
    lines = [
        "<details>",
        "<summary>Source evidence and report details</summary>",
        "",
        f"{report['total_candidates']} source entries; {report['accepted']} accepted; {report['unresolved']} unresolved identities; {report['watched_excluded']} watched entries excluded from suggestions.",
        f"Declared selection scope: {report['completeness']}. Declared lineage: {report['lineage']}",
    ]
    lines.extend(
        f"- {text(item['raw_title'])}: {source_reason(item)}; locator {text(item['locator'])}; published {text(item['published_at'])}; eligibility date {text(item['eligibility_date'])}; source completeness {text(item['source_completeness'])}; lineage {text(item['source_lineage_kind'])}: {text(item['source_lineage'])}; eligibility {text(item['source_eligibility'])}."
        for item in report["candidates"]
    )
    lines.extend(["", "</details>"])
    return lines


def markdown(report: dict) -> str:
    lines = [
        "# Your film shortlist",
        "",
        f"Personal history last refreshed: {text(report['last_successful_refresh'])}.",
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
            "Source reasons below describe public critical recognition, separate from your own ratings. Names and years follow the original source; film links open the reviewed catalog identity.",
            "",
            "## Suggested next",
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
