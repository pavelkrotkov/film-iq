"""Exact minor units with bounded currency support, never float or rounding guesses."""

import pytest

from film_iq.availability.candidate_fields import money


@pytest.mark.parametrize(
    "amount,currency,expected",
    [
        ("4.99", "USD", 499),
        ("100", "JPY", 100),
        ("1.234", "KWD", 1234),
        ("99999999999999999999999999999.99", "USD", 9999999999999999999999999999999),
    ],
)
def test_exact_supported_minor_units(amount, currency, expected):
    assert money({"amount": amount, "currency": currency}) == (expected, currency)


@pytest.mark.parametrize(
    "amount,currency",
    [
        (4.99, "USD"),
        (True, "USD"),
        ("1.005", "USD"),
        ("1.2", "JPY"),
        ("-1", "USD"),
        ("NaN", "USD"),
        ("Infinity", "USD"),
        ("1", "XXX"),
    ],
)
def test_invalid_or_unknown_price_never_becomes_free(amount, currency):
    with pytest.raises(ValueError):
        money({"amount": amount, "currency": currency})
