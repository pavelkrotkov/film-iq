"""Pure Access callers cannot turn a known positive free/ads price into zero cost."""

from datetime import date

import pytest

from film_iq.planning.models import Access, Film
from film_iq.planning.monthly import compare


@pytest.mark.parametrize("kind", ["free", "ads"])
@pytest.mark.parametrize("verified_only", [False, True])
@pytest.mark.parametrize("entitlement", ["confirmed", "unconfirmed"])
def test_positive_free_price_is_rejected_before_entitlement_filter(
    kind, verified_only, entitlement
):
    offers = [Access(1, 7, kind, entitlement, 999)]
    with pytest.raises(ValueError, match="free/ads access price"):
        compare(
            [Film(1, "Fixture", 90, 1)],
            offers,
            set(),
            [date(2026, 11, 1)],
            90,
            1,
            0,
            {},
            verified_only=verified_only,
        )


@pytest.mark.parametrize("price", [None, 0])
def test_zero_and_unknown_free_prices_remain_distinct(price):
    offer = Access(1, 7, "free", "unconfirmed", price)
    plan = compare([Film(1, "Fixture", 90, 1)], [offer], set(), [date(2026, 11, 1)], 90, 1, 0, {})[
        0
    ]
    assert plan.choices[0].offer.price_cents == price
    assert plan.feasibility == "tentative"
