"""Exact supported currency units and provider dates, with no guessed conversion."""

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

# Bounded ISO4217 subset, verified against SIX List One; unsupported codes reject.
EXPONENTS = {"USD": 2, "EUR": 2, "GBP": 2, "CAD": 2, "AUD": 2, "JPY": 0, "KWD": 3}


def money(value: dict | None) -> tuple[int | None, str | None]:
    if value is None:
        return None, None
    code, amount = value["currency"], value["amount"]
    if code not in EXPONENTS or not isinstance(amount, str):
        raise ValueError("unsupported currency or nondecimal price")
    try:
        number = Decimal(amount)
    except InvalidOperation:
        raise ValueError("invalid decimal price") from None
    if not number.is_finite() or number < 0:
        raise ValueError("price must be finite nonnegative exact minor units")
    numerator, denominator = number.as_integer_ratio()
    units, remainder = divmod(numerator * (10 ** EXPONENTS[code]), denominator)
    if remainder:
        raise ValueError("fractional minor currency unit")
    return units, code


def seconds(value: int | None) -> datetime | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise ValueError("provider date must be nonnegative Unix seconds")
    return datetime.fromtimestamp(value, UTC)


def link(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("public HTTPS source locator required")
    return value
