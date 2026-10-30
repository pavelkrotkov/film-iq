"""Movie of the Night v4 US options retain provider-asserted details."""

from typing import Any

from .provider_rows import offer


def motn_offer(row: dict[str, Any]) -> dict[str, Any]:
    kind = row["type"]
    if kind not in {"subscription", "free", "rent", "buy", "addon"}:
        raise ValueError("unsupported offer type")
    addon = row["addon"]["id"] if kind == "addon" else None
    if kind == "addon" and (not isinstance(addon, str) or not addon.strip()):
        raise ValueError("add-on ID must be a nonempty string")
    return offer(
        kind,
        row["service"]["id"],
        row["link"],
        addon=addon,
        source_details={
            key: row.get(key) for key in ("expiresOn", "availableSince", "expiresSoon", "price")
        },
    )


def motn_rows(data: dict[str, Any], film_id: str) -> list[dict[str, Any]]:
    """Only an explicitly returned US list can establish response completeness."""
    if data["imdbId"] != film_id or data["showType"] != "movie":
        raise ValueError("response identity differs")
    rows = data["streamingOptions"]["us"]
    if not isinstance(rows, list):
        raise ValueError("US options must be a list")
    return [motn_offer(row) for row in rows]
