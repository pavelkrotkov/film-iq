"""Present distinct recognition views without blending or changing report ordering."""

from film_iq.discovery_cards import card
from film_iq.discovery_order import public_support

SECTIONS = (
    "Critics' list choices",
    "Festival and award recognition",
    "Preservation and institutional selections",
    "Other source selections",
)


def _section(item: dict) -> str:
    kinds = {reason.get("evidence_kind") for reason in item.get("source_reasons", [item])}
    groups = item.get("public_evidence_components", {})
    kinds.update(
        kind
        for kind in (
            "critic_selection",
            "award_outcome",
            "registry_selection",
            "institutional_selection",
        )
        if groups.get(kind)
    )
    if "critic_selection" in kinds:
        return SECTIONS[0]
    if "award_outcome" in kinds:
        return SECTIONS[1]
    if kinds.intersection({"registry_selection", "institutional_selection"}):
        return SECTIONS[2]
    return SECTIONS[3]


def suggestion_sections(items: list[dict]) -> list[str]:
    """Keep each work and all its reasons in the first applicable evidence view."""
    groups = {name: [] for name in SECTIONS}
    for item in items:
        groups[_section(item)].append(item)
    lines = []
    for name, rows in groups.items():
        if rows:
            lines.extend(["", f"### {name}"])
        for item in rows:
            heading, *details = card(item)
            lines.extend(["", "#" + heading, *details])
    return lines


def ordering_sentence(items: list[dict], policy: str) -> str:
    if policy == "public-support" and any(
        _section(item) == SECTIONS[0] and public_support(item) is not None for item in items
    ):
        return "Critic-list choices use published source support; ties keep list order. Other sections keep source order."
    return "Source order is kept within each evidence section."
