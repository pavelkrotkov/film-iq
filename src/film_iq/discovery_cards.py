"""Readable film cards keep source reasons separate from the user's own judgments."""


def text(value):
    return "unknown" if value is None else str(value).replace("\n", " ")


def title(item: dict) -> str:
    name = f"{text(item['raw_title'])} ({text(item['year'])})"
    if item["identity_status"] == "reviewed" and item["tmdb_id"]:
        name = f"[{name}](https://www.themoviedb.org/movie/{item['tmdb_id']})"
    return f"{name} — {text(item['director'])}"


def source_reason(item: dict) -> str:
    rank = f"#{item['rank']}" if item["rank"] is not None else "unranked selection"
    tie = f" (tie: {item['tie']})" if item["tie"] else ""
    return f"{rank}{tie} in [{text(item['ballot_scope'])}: {text(item['edition'])}]({item['source_url']})"


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
    lines = [f"### {title(item)}", "", "Why consider it:"]
    lines.extend(f"- {source_reason(reason)}" for reason in reasons)
    if rating := personal(item):
        lines.extend(["", rating])
    if item["identity_status"] != "reviewed":
        lines.extend(["", "Film identity needs review before this can be recommended."])
    if item["extraction_status"] != "accepted":
        lines.extend(["", "The source selection still needs independent acceptance."])
    return lines
