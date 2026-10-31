"""Concise typed reasons retain meaning without adding a combined quality score."""

from film_iq.recognition.metric_render import metric_text
from film_iq.recognition.reader import group_components

LABELS = {
    "critic_selection": "critic ballots",
    "institutional_selection": "institutional selections",
    "registry_selection": "registry selections",
    "award_outcome": "awards",
    "reception_metric": "reception measurements",
}


def component_lines(groups: dict) -> list[str]:
    lines = []
    for kind in (
        "institutional_selection",
        "registry_selection",
        "award_outcome",
        "reception_metric",
    ):
        for row in groups[kind]:
            for value in row["component"] or []:
                lines.append(
                    f"- {_fact(kind, value)}. [Source]({row['url']}), published {row['published_at'] or 'unknown'}."
                )
    missing = ", ".join(LABELS[kind] for kind in groups["missing"])
    lines.append(
        f"Evidence coverage still unknown: {missing or 'additional sources'}. Missing evidence is not a negative judgment."
    )
    return lines


def _fact(kind: str, value: dict) -> str:
    if kind == "reception_metric":
        return metric_text(value)
    if kind == "award_outcome":
        return _award(value)
    # The source event edition is separate from the work's release cohort.
    label = "Registry selection" if kind == "registry_selection" else "Institutional selection"
    return f"{label}: {value['event']}, {value['edition']}; selection date {value['effective_on'] or 'unknown'}"


def report_lines(rows: list[dict]) -> list[str]:
    by_work = {}
    for row in rows:
        by_work.setdefault(row["tmdb_id"], []).append(row)
    lines = ["## Other public evidence"]
    for work, items in by_work.items():
        lines.extend(
            [
                f"### {items[0]['raw_title']} (TMDB {work or 'unknown'})",
                *component_lines(group_components(items)),
            ]
        )
    return lines


def _award(value: dict) -> str:
    # A performance prize belongs to its person recipient, not a Best Film category.
    recipient = (
        f"; recipient {value['recipient']} ({value['recipient_kind']})"
        if value["recipient"]
        else "; recipient unknown"
    )
    return (
        f"Award evidence: {value['event']}, {value['category'] or 'category unknown'} — "
        f"{value['outcome'] or 'outcome unknown'}{recipient}; "
        f"edition {value['edition'] or 'unknown'}, event date {value['effective_on'] or 'unknown'}"
    )
