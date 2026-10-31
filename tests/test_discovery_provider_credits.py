"""Known providers carry prescribed visible credit even with a generic operator note."""

from discovery_fixtures import accept_source, cohort, fresh_status, snapshot
from display_fixtures import NOW, catalog_path, payload

from film_iq.discovery import build_discovery
from film_iq.discovery_credits import TMDB_LOGO, visible_credits
from film_iq.discovery_presentation import present_discovery
from film_iq.discovery_render import markdown


def test_tmdb_catalog_credit_is_visible_and_logo_links_home(evidence_db, tmp_path):
    accept_source(evidence_db)
    raw = build_discovery(cohort(), snapshot(), db=evidence_db, refresh_status=fresh_status())
    value = payload()
    value["attribution"] = "TMDB reviewed metadata"
    rendered = markdown(present_discovery(raw, catalog_path(tmp_path, value), now=NOW)).split(
        "<details>", 1
    )[0]
    assert f'<a href="https://www.themoviedb.org/"><img src="{TMDB_LOGO}"' in rendered
    assert 'width="120"' in rendered
    assert "This product uses the TMDB API but is not endorsed or certified by TMDB." in rendered


def test_named_tmdb_watch_rows_also_credit_justwatch():
    state = {"attribution": "Operator credit", "latest_attempt": {"source": "tmdb"}}
    output = " ".join(visible_credits({"candidates": [{"offer_states": [state, state]}]}))
    assert output.count(TMDB_LOGO) == 1
    assert "[JustWatch](https://www.justwatch.com/)" in output
