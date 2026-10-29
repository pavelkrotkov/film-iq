"""Concise Markdown rendering of a dry-run report with explicit identity links."""


def _citation(item: dict, treatment: str) -> str:
    """Keep publication and dependence context beside each source citation."""
    return (
        f"  - {treatment}: [{item['author'] or item['list_id']}]({item['url']}): "
        f"list {item['list_id']}, rank {item['rank'] or 'unknown'}, "
        f"{item['completeness'] or 'unknown completeness'}; "
        f"published {item['published'] or 'unknown'}; eligibility {item['eligibility']}; "
        f"independence group {item['independence_group']}; "
        f"lineage {item['lineage_kind'] or 'unknown'}: {item['lineage'] or 'unknown'}; "
        f"derivative of {', '.join(item['derivative_of']) or 'not specified'}."
    )


def _evidence(report: dict) -> list[str]:
    # Excluded observations explain dependence; they never add endorsements.
    lines = ["## Why these films matter"]
    for result in report["evidence"]:
        tmdb = report["crosswalk"].get(result["film_id"], "unresolved")
        lines.append(
            f"- Film {result['film_id']} → TMDB {tmdb}: {result['independent_count']} independent endorsements; {result['partial_count']} partial lists; {result['unranked_count']} unknown ranks."
        )
        lines.extend(_citation(item, "Contributing") for item in result["contributing"])
        lines.extend(
            _citation(item, "Excluded from independent count") for item in result["excluded"]
        )
    return lines


def _offer_key(offer: dict) -> tuple:
    """Use the shared identity in planner access and normalized source offers."""
    return offer["film_id"], offer["provider_id"], offer["kind"]


def _choice(choice: dict, offers: dict) -> str:
    # Source names/URLs supplement access; entitlement stays the planner's value.
    access = choice["offer"]
    offer = offers.get(_offer_key(access))
    provider = f"provider {access['provider_id']} (details unknown)"
    if offer:
        provider = (
            f"[{offer['provider']}]({offer['url']}) (provider {access['provider_id']}), "
            f"checked {offer['checked_at']} ({offer['source']})"
        )
    return (
        f"- {choice['film']['title']} (TMDB {choice['film']['id']}), "
        f"{choice['film']['minutes']} minutes: {access['kind']}, {provider}, "
        f"entitlement {access['entitlement']}, {choice['viewing_date']}."
    )


def _plans(report: dict) -> list[str]:
    # A provider can supply multiple access kinds for the same film.
    lines = ["## Viewing options"]
    offers = {
        _offer_key(offer): offer
        for observation in report["offers"]
        for offer in observation["offers"]
    }
    for plan in report["plans"]:
        lines.append(
            f"### {plan['option']} — USD {plan['cost_cents'] / 100:.2f}, {plan['total_minutes']} minutes"
        )
        lines.append(plan["assumptions"])
        lines.extend(_choice(choice, offers) for choice in plan["choices"])
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
