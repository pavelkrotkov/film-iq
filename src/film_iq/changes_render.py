"""Concise local changes; source absence is never inferred."""


def markdown(result: dict) -> str:
    lines = [
        "# Film IQ — local changes",
        f"Assessed {result['assessed_at']}.",
        result["acknowledgement"],
    ]
    if result["baseline"]:
        lines.append(
            "First-use baseline: existing accepted sources and retained offers are not alerts."
        )
    for item in result["source_changes"]:
        action = "Updated" if item["previous_revision_id"] else "New"
        lines.append(
            f"- {action} accepted source: [{item['source']}]({item['url']}); fetched {item['accessed_at']}."
        )
    lines.extend(_offer(item["change"]) for item in result["offer_changes"])
    if not result["baseline"] and not (result["source_changes"] or result["offer_changes"]):
        lines.append("No new retained changes.")
    return "\n\n".join(lines) + "\n"


def _offer(change: dict) -> str:
    offer = change["opportunity"]
    action = {
        "source_first_seen": "newly reports",
        "source_absent": "no longer reports",
    }[change["kind"]]
    return f"- Source {change['source']} {action} [TMDB {offer['film_id']}](https://www.themoviedb.org/movie/{offer['film_id']}) on {offer['service']} / {offer['plan'] or 'unknown plan'} in its complete snapshot; observed {change['observed_at']}."
