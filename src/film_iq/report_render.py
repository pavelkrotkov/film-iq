"""Concise Markdown rendering of a dry-run report with explicit identity links."""


def _evidence(report: dict) -> list[str]:
    lines = ["## Why these films matter"]
    for result in report["evidence"]:
        tmdb = report["crosswalk"].get(result["film_id"], "unresolved")
        lines.append(
            f"- Film {result['film_id']} → TMDB {tmdb}: {result['independent_count']} independent endorsements; {result['partial_count']} partial lists; {result['unranked_count']} unknown ranks."
        )
        lines.extend(
            f"  - [{item['author'] or item['list_id']}]({item['url']}): rank {item['rank'] or 'unknown'}, {item['completeness'] or 'unknown completeness'}."
            for item in result["contributing"]
        )
    return lines


def _plans(report: dict) -> list[str]:
    lines = ["## Viewing options"]
    for plan in report["plans"]:
        lines.append(
            f"### {plan['option']} — USD {plan['cost_cents'] / 100:.2f}, {plan['total_minutes']} minutes"
        )
        lines.append(plan["assumptions"])
        lines.extend(
            f"- {choice['film']['title']} (TMDB {choice['film']['id']}), {choice['film']['minutes']} minutes: {choice['offer']['kind']}, entitlement {choice['offer']['entitlement']}, {choice['viewing_date']}."
            for choice in plan["choices"]
        )
    return lines


def markdown(report: dict) -> str:
    lines = ["# Film IQ — dry-run viewing report", "", report["assumptions"], ""]
    lines.extend(_evidence(report))
    lines.extend(_plans(report))
    lines.append("## Provider snapshots")
    lines.extend(
        f"- TMDB {item['tmdb_id']}: {item['status']}, checked {item['checked_at']} (TMDB / JustWatch)."
        for item in report["offers"]
    )
    lines.append("## Watchlist previews")
    lines.extend(f"- {preview}" for previews in report["previews"].values() for preview in previews)
    return "\n\n".join(lines) + "\n"
