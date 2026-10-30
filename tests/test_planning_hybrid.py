"""C5 hybrid, verification and declared-utility regression examples."""

from datetime import date

from film_iq.planning.models import Access, Film
from film_iq.planning.monthly import compare

DAY = date(2026, 11, 1)


def plans(films, offers, **kwargs):
    return compare(films, offers, set(), [DAY, date(2026, 11, 8)], 180, 2, 1000, {1: 500}, **kwargs)


def test_subscription_plus_rental_is_distinct_and_not_double_counted():
    films = [Film(1, "Subscription", 90, 8), Film(2, "Rental", 90, 7)]
    offers = [
        Access(1, 1, "subscription", "confirmed"),
        Access(1, 2, "rent", "confirmed", 200),
        Access(2, 2, "rent", "confirmed", 300),
    ]
    hybrid = plans(films, offers)[-1]
    assert (hybrid.option, hybrid.utility, hybrid.cost_cents) == ("service 1 + rentals", 15, 800)
    assert len({choice.film.id for choice in hybrid.choices}) == 2
    assert hybrid.feasibility == "verified"


def test_verified_search_preserves_lower_utility_confirmed_option():
    films = [Film(1, "Unconfirmed", 90, 8), Film(2, "Confirmed", 90, 7)]
    offers = [
        Access(1, 1, "subscription", "unconfirmed"),
        Access(2, 1, "subscription", "confirmed"),
    ]
    tentative = plans(films, offers)[-1]
    verified = plans(films, offers, verified_only=True)[-1]
    assert tentative.utility == 15 and tentative.feasibility == "tentative"
    assert verified.utility == 7 and verified.feasibility == "verified"
