"""Attach typed public facts and keep full missingness outside the main shortlist."""

from film_iq.recognition.reader import current_components, group_components
from film_iq.recognition.render import component_lines


def attach_components(items: list[dict], db) -> list[dict]:
    by_work, by_entry = {}, {}
    for row in current_components(db) if db is not None else []:
        by_entry.setdefault((row["entry_id"], row["revision_id"]), []).append(row)
        if row["tmdb_id"] is not None:
            by_work.setdefault(row["tmdb_id"], []).append(row)
    return [_attach(item, by_work, by_entry) for item in items]


def _attach(item, by_work, by_entry):
    rows = (
        by_work.get(item["tmdb_id"], [])
        if item["identity_status"] == "reviewed"
        else by_entry.get((item.get("entry_id"), item.get("revision_id")), [])
    )
    return {**item, "public_evidence_components": group_components(rows)}


def award_reasons(item: dict) -> list[str]:
    lines = []
    for row in item.get("public_evidence_components", {}).get("award_outcome", []):
        for award in row["component"]:
            if award["recipient"] and award["category"] and award["outcome"]:
                lines.append(
                    f"- [{award['event']}]({row['url']}): {award['recipient']} — {award['category']} ({award['outcome']})."
                )
    return lines


def audit_components(items: list[dict]) -> list[str]:
    seen, lines = set(), []
    for item in items:
        work = item["tmdb_id"] or (item.get("entry_id"), item.get("revision_id"))
        if work in seen or "public_evidence_components" not in item:
            continue
        seen.add(work)
        lines.extend(
            [
                f"#### {item['raw_title']}: separate public evidence",
                *component_lines(item["public_evidence_components"]),
            ]
        )
    return lines
