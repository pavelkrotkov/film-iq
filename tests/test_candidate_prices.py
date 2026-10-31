"""Exact minor units with bounded currency support, never float or rounding guesses."""

import pytest

from film_iq.availability.candidate_fields import money


def test_exact_supported_minor_units():
    amount, currency, expected = "4.99", "USD", 499
    assert money({"amount": amount, "currency": currency}) == (expected, currency)


def test_invalid_or_unknown_price_never_becomes_free():
    amount, currency = 4.99, "USD"
    with pytest.raises(ValueError):
        money({"amount": amount, "currency": currency})
