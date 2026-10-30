"""C5 hybrid, verification and declared-utility regression examples."""

from datetime import date

from film_iq.planning.models import Access, Film
from film_iq.planning.monthly import compare

DAY = date(2026, 11, 1)


def plans(films, offers, **kwargs):
    return compare(films, offers, set(), [DAY, date(2026, 11, 8)], 180, 2, 1000, {1: 500}, **kwargs)


def test_unknown_price_is_excluded_and_expiry_is_not_guessed():
    films = [Film(1, "Unknown rental", 90, 8), Film(2, "Unknown subscription", 90, 7)]
    offers = [Access(1, 2, "rent", "confirmed"), Access(2, 1, "subscription", "confirmed")]
    result = compare(films, offers, set(), [DAY], 180, 2, 1000, {1: None})
    assert len(result) == 2 and all(not plan.choices for plan in result)
    assert all("Unknown prices are excluded" in plan.assumptions for plan in result)


def test_declared_sensitivity_can_prefer_exceptional_over_many_good():
    films = [
        Film(1, "Exceptional", 180, 10, personal_enjoyment=4, personal_artistic_merit=9),
        Film(2, "Good one", 90, 6),
        Film(3, "Good two", 90, 6),
    ]
    offers = [Access(film.id, 1, "subscription", "confirmed") for film in films]
    additive = plans(films, offers)[-1]
    exceptional = plans(films, offers, utility_power=2)[-1]
    assert [choice.film.id for choice in additive.choices] == [2, 3]
    choice = exceptional.choices[0]
    assert choice.film.id == 1 and exceptional.utility == 100
    assert (choice.film.personal_enjoyment, choice.film.personal_artistic_merit) == (4, 9)
    assert "recognition-power-v1 power=2" in exceptional.assumptions
