"""Personal UI preview, confirmation, preserved state and truthful failure workflow."""

import re
from urllib.parse import urlencode

from web_movary_dates import inspect_dates, inspect_failure
from web_movary_stub import MovaryStub
from web_support import request

from film_iq import web_movary_api, web_movary_refresh
from film_iq.web_movary import MovaryControls


def post(app, route, values):
    return request(
        app,
        "/films/123/movary/" + route,
        method="POST",
        body=urlencode({"csrf_token": app.csrf_token, **values}),
    )


def approve(app, action, values=None):
    preview = post(app, action + "/preview", values or {})
    assert preview["status"] == "200 OK"
    match = re.search(r'name="signature" value="([a-f0-9]+)"', preview["body"])
    assert match is not None
    return {**(values or {}), "signature": match[1]}


def inspect_movary(app, root, monkeypatch):
    missing = request(app, "/films/123")["body"]
    assert "Movary actions are unavailable" in missing
    stub = MovaryStub(root)
    with monkeypatch.context() as patch:
        patch.setenv("MOVARY_URL", "https://movary.example.test")
        patch.setenv("MOVARY_USERNAME", "fixture")
        patch.setenv("MOVARY_TOKEN", "PRIVATE TOKEN")
        patch.setattr(web_movary_api, "MovaryClient", lambda *_: stub)
        patch.setattr(web_movary_api, "MovaryHTTPTransport", lambda *_: stub)
        patch.setattr(web_movary_refresh, "refresh", stub.refresh)
        app.movary = MovaryControls(app.snapshot, ["fixture-ratings"], ["fixture-history"])
        post(app, "refresh", {})
        page = request(app, "/films/123")["body"]
        assert 'href="https://movary.example.test/users/fixture/movies/456"' in page
        assert "Edit enjoyment rating in Movary" in page
        assert "PRIVATE" not in page
        inspect_watchlist(app, stub)
        inspect_dates(app, stub, post, approve)
        inspect_failure(app, stub, patch, post, approve)


def inspect_watchlist(app, stub):
    confirmation = approve(app, "watchlist")
    assert stub.calls == []  # Neither rendering nor preview makes an API request.
    refused = post(app, "watched/confirm", {**confirmation, "date": "2026-02-02"})
    assert refused["status"].startswith("403")
    assert stub.calls == []
    assert "Added to watchlist" in post(app, "watchlist/confirm", confirmation)["body"]
    assert stub.watchlisted
    writes = len(stub.calls)
    assert "Already on watchlist" in post(app, "watchlist/confirm", confirmation)["body"]
    assert all(call[0] == "GET" for call in stub.calls[writes:])
