"""Validate explicit component facts without converting units or unknowns."""

from datetime import date


def names(*values: str) -> None:
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError("component names and provenance must be nonblank strings")


def day(value: date | None) -> None:
    if value is not None and type(value) is not date:
        raise ValueError("component date must be an exact date or unknown")


def count(value: int | None) -> None:
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError("sample count must be a nonnegative integer or unknown")


def award_recipient(value: str | None, kind: str | None) -> None:
    if value is not None:
        names(value)
    if (value is None) != (kind is None):
        raise ValueError("known award recipients require their explicit type")
    if kind not in {None, "film", "person", "ensemble"}:
        raise ValueError("unsupported award recipient type")
