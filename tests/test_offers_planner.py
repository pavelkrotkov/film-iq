from datetime import date

from film_iq.planning.monthly import Access, Film, compare


def test_bundle_compares_access_cost_overlap_and_expiry():
    films = [
        Film(1, "One", 90, 10),
        Film(2, "Two", 60, 8),
        Film(3, "Three", 60, 7),
        Film(4, "Watched", 30, 100, True),
    ]
    offers = [
        Access(1, 1, "subscription", "confirmed"),
        Access(1, 2, "subscription", "unconfirmed"),
        Access(2, 2, "subscription", "unconfirmed", expires=date(2026, 11, 1)),
        Access(3, 3, "rent", "unconfirmed", 300),
        Access(4, 2, "subscription", "confirmed"),
        Access(3, 2, "subscription", "unavailable_on_plan"),
    ]
    plans = compare(
        films, offers, {1}, [date(2026, 11, 1), date(2026, 11, 8)], 150, 2, 1000, {2: 700}
    )
    base, rental, service, _hybrid = plans
    assert [c.film.id for c in base.choices] == [1]
    assert rental.utility == 17 and rental.cost_cents == 300
    assert service.utility == 18 and service.cost_cents == 700 and service.total_minutes == 150
    assert [(c.film.id, c.viewing_date) for c in service.choices] == [
        (2, date(2026, 11, 1)),
        (1, date(2026, 11, 8)),
    ]
    assert "tentative" in service.assumptions
    assert compare(films, offers, {1}, [date(2026, 11, 8)], 150, 2, 500, {2: 700})[0].utility == 10


def test_add_on_requires_confirmed_existing_access():
    films = [Film(i, str(i), 60, 1) for i in range(1, 5)]
    offers = [
        Access(1, 1, "add-on", "confirmed"),
        Access(2, 1, "add-on", "unconfirmed"),
        Access(3, 1, "add-on", "unavailable_on_plan"),
        Access(4, 2, "add-on", "confirmed"),
    ]
    plans = compare(
        films, offers, {1}, [date(2026, 11, day) for day in range(1, 5)], 240, 4, 1000, {2: 500}
    )
    assert [[choice.film.id for choice in plan.choices] for plan in plans] == [[1], [1], [1], [1]]
