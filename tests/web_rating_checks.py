"""The combined rating/watch steps extend the existing user journey."""

import json
import subprocess
from types import SimpleNamespace

from web_support import request

from film_iq import web_movary_rating


def inspect_rating(app, stub, patch, post, approve):
    app.movary.rating_command = ["fixture-rating-service"]
    assert 'name="rating"' in request(app, "/films/123")["body"]
    calls = []

    def run(command, *, input, **kwargs):
        payload = json.loads(input)
        assert command == app.movary.rating_command
        assert kwargs["stderr"] == subprocess.DEVNULL
        calls.append(payload)
        stub.rating = payload["rating"]
        return SimpleNamespace(stdout=json.dumps({"tmdb_id": 123, "rating": stub.rating}))

    patch.setattr(web_movary_rating.subprocess, "run", run)
    values = {"date": "2026-04-04", "rating": "9"}
    preview = post(app, "rated-watched/preview", values)
    assert "9/10" in preview["body"] and calls == []
    confirmation = approve(app, "rated-watched", values)
    assert (
        post(app, "rated-watched/confirm", {**confirmation, "rating": "8"})["status"]
        == "403 Forbidden"
    )
    saved = post(app, "rated-watched/confirm", confirmation)
    assert "Enjoyment rating 9/10 saved" in saved["body"]
    inspect_rating_retry(app, stub, calls, post, approve, confirmation)
    inspect_rating_failure(app, stub, patch, post, approve, run)


def inspect_rating_retry(app, stub, calls, post, approve, confirmation):
    dates = list(stub.dates)
    post(app, "rated-watched/confirm", confirmation)
    assert stub.dates == dates
    assert calls[-1] == {"username": "fixture", "tmdb_id": 123, "rating": 9}
    assert json.loads(app.snapshot.read_text())["films"][0]["personal_enjoyment"] == 9
    # A blank rating logs the date while retaining the existing score.
    blank = approve(app, "rated-watched", {"date": "2026-04-05", "rating": ""})
    count = len(calls)
    post(app, "rated-watched/confirm", blank)
    assert len(calls) == count and stub.rating == 9


def inspect_rating_failure(app, stub, patch, post, approve, run):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["fixture-rating-service"])

    confirmation = approve(app, "rated-watched", {"date": "2026-04-06", "rating": "8"})
    patch.setattr(web_movary_rating.subprocess, "run", fail)
    failed = post(app, "rated-watched/confirm", confirmation)
    assert "Watch date saved in Movary" in failed["body"]
    assert failed["status"] == "502 Bad Gateway"
    assert json.loads(app.snapshot.with_suffix(".json.status").read_text())["stale"]
    dates = list(stub.dates)
    patch.setattr(web_movary_rating.subprocess, "run", run)
    post(app, "rated-watched/confirm", confirmation)
    assert stub.dates == dates and stub.rating == 8
