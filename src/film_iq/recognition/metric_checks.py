"""Validate unlike reception measurements separately, with no unit conversion."""

from math import isfinite

from film_iq.recognition.checks import names


def measurement(metric: str, value, unit: str | None) -> None:
    allowed = {
        "positivity": {"percent"},
        "mean": {"score_100", "score_10", "score_5"},
        "count": {"count"},
        "grade": {"grade"},
    }
    if metric not in allowed or (unit is not None and unit not in allowed[metric]):
        raise ValueError("metric and original unit must agree")
    if value is None:
        return
    if unit is None:
        raise ValueError("known reception values require an explicit original unit")
    if metric == "grade":
        names(value)
        return
    numeric(value, unit)


def numeric(value, unit: str) -> None:
    if type(value) not in {int, float} or not isfinite(value):
        raise ValueError(
            "reception values must be finite numbers, never booleans or numeric strings"
        )
    limits = {"percent": 100, "score_100": 100, "score_10": 10, "score_5": 5}
    if value < 0 or value > limits.get(unit, float("inf")):
        raise ValueError("reception value outside its original unit range")
    if unit == "count" and type(value) is not int:
        raise ValueError("reception counts must be integers")
