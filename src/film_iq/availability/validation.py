"""Small shared checks at provider-neutral observation boundaries."""

from datetime import datetime


def aware(value: datetime) -> None:
    if value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")


def positive_id(value: int) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError("positive film ID required")


def required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("source, service and provenance must be nonblank")


def optional_names(values: tuple[str | None, ...]) -> None:
    for value in values:
        if value is not None:
            required(value)


def code(value: str, length: int) -> None:
    if not (len(value) == length and value.isascii() and value.isalpha() and value.isupper()):
        raise ValueError("country/currency must be an explicit uppercase code")


def price(value: int | None) -> None:
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError("price must be nonnegative minor currency units or unknown")


def source_scope(source: str, film_id: int, country: str, plan: str | None) -> None:
    required(source)
    positive_id(film_id)
    code(country, 2)
    optional_names((plan,))
