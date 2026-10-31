"""Unknown departure is uncertainty, not verified future access or zero utility."""

from datetime import date

from film_iq.planning.models import Access, Film
from film_iq.planning.monthly import compare

DAY = date(2026, 11, 1)


def test_unknown_expiry_retains_confirmed_entitlement_and_exploratory_utility():
    film = Film(1, "Fixture", 90, 8)
    offer = Access(1, 7, "free", "confirmed", 0)
    parameters = ([film], [offer], set(), [DAY], 90, 1, 0, {})
    exploratory = compare(*parameters)[0]
    verified = compare(*parameters, verified_only=True)[0]
    assert exploratory.feasibility == "tentative" and exploratory.utility == 8
    assert exploratory.choices[0].offer == offer
    assert verified.choices == () and verified.cost_cents == 0


def test_verified_search_preserves_lower_utility_known_expiry_alternative():
    films = [Film(1, "Unknown expiry", 90, 8), Film(2, "Known expiry", 90, 7)]
    offers = [Access(1, 7, "free", "confirmed", 0), Access(2, 7, "free", "confirmed", 0, DAY)]
    parameters = (films, offers, set(), [DAY], 90, 1, 0, {})
    exploratory = compare(*parameters)[0]
    verified = compare(*parameters, verified_only=True)[0]
    assert exploratory.utility == 8 and exploratory.feasibility == "tentative"
    assert verified.utility == 7 and verified.feasibility == "verified"
    assert verified.choices[0].film.id == 2
