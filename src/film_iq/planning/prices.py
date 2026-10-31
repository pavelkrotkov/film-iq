"""Reject contradictory free-access prices at every planner input boundary."""


def validate_free_price(kind: str, price: int | None) -> None:
    if kind in {"free", "ads"} and price not in (None, 0):
        raise ValueError("free/ads access price must be zero or unknown")
