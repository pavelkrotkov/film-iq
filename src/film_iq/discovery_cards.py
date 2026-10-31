"""Readable film cards keep source reasons separate from the user's own judgments."""

from film_iq.discovery_display_card import display_details
from film_iq.discovery_display_card import text as text
from film_iq.discovery_display_card import title as title
from film_iq.discovery_offer_render import offer_lines
from film_iq.recognition.discovery import award_reasons


def source_reason(item: dict) -> str:
    rank = f"#{item['rank']} — " if item["rank"] is not None else ""
    tie = " (tied)" if item["tie"] else ""
    label = text(item["ballot_scope"]).replace(" / ", " — ")
    kind = item.get("evidence_kind", "unknown")
    prefix = {
        "registry_selection": "Registry selection — ",
        "institutional_selection": "Institutional selection — ",
        "award_outcome": "Award source — ",
        "reception_metric": "Reception source — ",
    }.get(kind, "")
    return f"{prefix}{rank}[{label}]({item['source_url']}){tie}"


def personal(item: dict) -> str:
    enjoyment, artistic = item["personal_enjoyment"], item["personal_artistic_merit"]
    if (enjoyment, artistic, item["merit_status"]) == (None, None, "unknown"):
        return ""
    merit = (
        "unknown — needs review"
        if item["merit_status"] in {"invalid", "conflict"}
        else _rating(artistic)
    )
    return f"Your ratings: enjoyment {_rating(enjoyment)}; artistic merit {merit}."


def _rating(value):
    return "unknown" if value is None else f"{value}/10"


def card(item: dict) -> list[str]:
    reasons = item.get("source_reasons", [item])
    lines = [f"### {title(item)}", "", *display_details(item), "", "Why consider it:"]
    lines.extend(f"- {source_reason(reason)}" for reason in reasons)
    lines.extend(award_reasons(item))
    lines.extend(offer_lines(item))
    if rating := personal(item):
        lines.extend(["", rating])
    if item["identity_status"] != "reviewed":
        lines.extend(["", "Film identity needs review before this can be recommended."])
    if item["extraction_status"] != "accepted":
        lines.extend(["", "The source selection still needs independent acceptance."])
    return lines
