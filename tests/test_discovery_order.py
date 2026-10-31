"""Support counts stay separate from ranks, missing evidence and personal scores."""

from typing import cast

import pytest

from film_iq.discovery_order import Order, ordered_suggestions


def item(name, support, rank=None):
    return {
        "name": name,
        "rank": rank,
        "personal_enjoyment": 10,
        "external_critical_recognition": None
        if support is None
        else {"independent_count": support},
    }


def test_support_order_keeps_unknown_slots_and_stable_unranked_ties():
    rows = [item("a", 1, 1), item("unknown", None), item("b", 3), item("c", 3, 9), item("zero", 0)]
    result = ordered_suggestions(rows, "public-support")
    assert [row["name"] for row in result] == ["b", "unknown", "c", "a", "zero"]
    assert result[1]["external_critical_recognition"] is None
    assert rows[0]["rank"] == 1 and result[0]["rank"] is None
    assert ordered_suggestions(rows) == rows


def test_unknown_policy_does_not_silently_change_order():
    with pytest.raises(ValueError, match="order"):
        ordered_suggestions([], cast(Order, "invalid"))
