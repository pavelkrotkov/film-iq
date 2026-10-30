"""Conservative normalization for one US response, never removal inference."""

from typing import Any


def offer(kind: str, service: str, link: str, **extra: Any) -> dict[str, Any]:
    if not isinstance(service, str) or not service or not link.startswith("https://"):
        raise ValueError("missing service or HTTPS locator")
    return {"type": kind, "service": service, "link": link, "entitlement": "unknown", **extra}


def tmdb_provider_id(row: dict[str, Any]) -> str:
    value = row["provider_id"]
    if type(value) is not int or value <= 0:
        raise ValueError("provider ID must be a positive integer")
    return str(value)


def tmdb_rows(data: dict[str, Any], film_id: str) -> list[dict[str, Any]]:
    """Require the explicit US object; an absent country is not an empty offer list."""
    if data["id"] != int(film_id):
        raise ValueError("response identity differs")
    region = data["results"]["US"]
    link = region["link"]
    if not link.startswith("https://"):
        raise ValueError("missing HTTPS region locator")
    kinds = {"flatrate": "subscription", "free": "free", "ads": "ads", "rent": "rent", "buy": "buy"}
    if set(region) - {"link", *kinds}:
        raise ValueError("unsupported offer category")
    if any(not isinstance(region.get(category, []), list) for category in kinds):
        raise ValueError("offer categories must be lists")
    return [
        offer(kind, tmdb_provider_id(row), link, attribution="JustWatch via TMDB")
        for category, kind in kinds.items()
        for row in region.get(category, [])
    ]
