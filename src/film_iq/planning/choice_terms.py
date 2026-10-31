"""Expose known cost and distinct scheduling/source expiry without charging fees twice."""


def choice_terms(access: dict, source: dict | None) -> str:
    expiry = source.get("asserted_expires_at") if source else None
    return (
        f"{_cost(access)}; last full viewing day {access.get('expires') or 'unknown'}; "
        f"provider-asserted expiry {expiry or 'unknown'}"
    )


def _cost(access: dict) -> str:
    value = access.get("price_cents")
    price = "unknown" if value is None else f"USD {value / 100:.2f}"
    if access["kind"] == "subscription":
        return f"subscription fee assumption {price} (existing fees are sunk; new-service fee counted once in plan total)"
    if access["kind"] == "add-on":
        return f"existing add-on fee assumption {price} (sunk; no additional per-film fee)"
    label = "one-off rental" if access["kind"] == "rent" else "access"
    return f"{label} price {price}"
