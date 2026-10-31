"""Expose known cost and distinct scheduling/source expiry without charging fees twice."""


def choice_terms(access: dict, source: dict | None, service_prices: dict | None = None) -> str:
    expiry = source.get("asserted_expires_at") if source else None
    return (
        f"{_cost(access, service_prices or {})}; last full viewing day {access.get('expires') or 'unknown'}; "
        f"provider-asserted expiry {expiry or 'unknown'}"
    )


def _price(access: dict, service_prices: dict) -> tuple[int | None, str]:
    value = access.get("price_cents")
    declared = service_prices.get(str(access["provider_id"]))
    if access["kind"] == "subscription" and value is None and declared is not None:
        return declared, "caller-declared "
    return value, ""


def _cost(access: dict, service_prices: dict) -> str:
    value, origin = _price(access, service_prices)
    price = "unknown" if value is None else f"USD {value / 100:.2f}"
    if access["kind"] == "subscription":
        return f"{origin}subscription fee assumption {price} (existing fees are sunk; new-service fee counted once in plan total)"
    if access["kind"] == "add-on":
        return f"existing add-on fee assumption {price} (sunk; no additional per-film fee)"
    label = "one-off rental" if access["kind"] == "rent" else "access"
    return f"{label} price {price}"
