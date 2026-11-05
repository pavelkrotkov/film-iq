"""Watch logging preserves old personal state, including after an uncertain write."""

import json

from film_iq import web_movary_refresh


def inspect_dates(app, stub, post, approve):
    assert post(app, "watched/preview", {"date": ""})["status"] == "400 Bad Request"
    values = {"date": "2026-02-02"}
    preview = post(app, "watched/preview", values)
    assert "may remove this film from your watchlist" in preview["body"]
    confirmation = approve(app, "watched", values)
    assert "Watch date saved in Movary" in post(app, "watched/confirm", confirmation)["body"]
    assert not stub.watchlisted
    assert stub.dates[0] == {"date": "2026-01-01", "plays": 2, "comment": "PRIVATE KEEP COMMENT"}
    inspect_retry(app, stub, post, confirmation)


def inspect_retry(app, stub, post, confirmation):
    before = list(stub.dates)
    assert "already recorded" in post(app, "watched/confirm", confirmation)["body"]
    assert stub.dates == before
    cached = json.loads(app.snapshot.read_text())["films"][0]
    assert cached["personal_enjoyment"] == 7
    assert cached["watched_dates"] == ["2026-01-01", "2026-02-02"]


def inspect_failure(app, stub, patch, post, approve):
    # Lose a response after the API committed: the UI must not claim a rollback.
    confirmation = approve(app, "watched", {"date": "2026-03-03"})
    stub.uncertain = True
    failed = post(app, "watched/confirm", confirmation)
    assert failed["status"].startswith("502")
    assert "may have been saved" in failed["body"]
    assert "PRIVATE API RESPONSE" not in failed["body"]
    assert json.loads(app.snapshot.with_suffix(".json.status").read_text())["stale"]
    stub.uncertain = False
    # The next verified write survives a separate complete-export failure.
    patch.setattr(
        web_movary_refresh, "refresh", lambda *a, **k: (_ for _ in ()).throw(ValueError())
    )
    saved = post(app, "watchlist/confirm", approve(app, "watchlist"))
    assert "Added to watchlist in Movary" in saved["body"]
    assert "FilmIQ refresh failed" in saved["body"]
