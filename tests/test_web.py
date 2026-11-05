"""One browser-facing journey through accepted evidence and optional personal state."""

import json

from discovery_fixtures import fresh_status, snapshot
from display_fixtures import NOW
from web_disposition_support import inspect_dispositions
from web_movary_checks import inspect_movary
from web_support import inspect_aliases, inspect_offer_identity, prepare, request

from film_iq import web


def inspect_evidence(app):
    # Source facts remain inspectable even when reviewed display facts differ.
    page = request(app, "/films/123")["body"]
    assert 'href="https://example.test/list"' in page
    assert "Rank #2 · tied (group-a)" in page
    assert "A &lt;script&gt;alert(1)&lt;/script&gt; Film" in page
    assert "<script>" not in page
    assert "Original film title" in page
    assert "Reviewed English title" in page
    inspect_award(page)


def inspect_award(page):
    # A performance winner belongs to the person, not a fabricated Best Film prize.
    assert "Fixture Actor (person)" in page
    assert "Performance" in page
    assert "prize" in page
    assert "Catalog release dates do not rewrite source-listed years" in page
    assert "Lineage kind" in page
    assert "Evidence coverage unknown" in page
    assert "Streaming, rental prices and your plan entitlement are unknown" in page


def inspect_personal(app, root):
    personal = root / "personal.json"
    personal.write_text(json.dumps(snapshot(True)))
    status = personal.with_suffix(".json.status")
    status.write_text(json.dumps(fresh_status()))
    app.snapshot = personal
    assert "0 films to explore" in request(app)["body"]
    assert "1 film to explore" in request(app, "/?watched=watched")["body"]
    detail = request(app, "/films/123")["body"]
    inspect_private_notes(detail)
    # A failed refresh makes current exclusion unknown, without hiding the film.
    status.write_text(json.dumps({**fresh_status(), "stale": True}))
    assert "1 film to explore" in request(app)["body"]
    assert "Watch history unknown" in request(app)["body"]
    assert "0 films to explore" in request(app, "/?watched=watched")["body"]


def inspect_private_notes(detail):
    # Public recognition must not expose private export/comment provenance.
    assert "Your enjoyment /10" in detail
    assert "conflicting or invalid" in detail
    assert "PRIVATE COMMENT" not in detail


def inspect_browse(app):
    home = request(app)
    assert home["status"] == "200 OK"
    assert "1 film to explore" in home["body"]
    assert "Watch history unknown" in home["body"]
    assert home["headers"]["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in home["headers"]["Content-Security-Policy"]
    assert (
        "1 film to explore"
        in request(app, "/?q=REVIEWED+DIRECTOR&kind=award_outcome&order=source")["body"]
    )
    assert "No films match these filters" in request(app, "/?q=another+film")["body"]


def inspect_missing(app, db, root):
    # Losing reviewed identity removes the detail route; input failure is not absence.
    db.execute("DELETE FROM current_match")
    db.commit()
    assert request(app, "/films/123")["status"].startswith("404")
    app.cohort = root / "missing.json"
    failed = request(app)
    assert failed["status"].startswith("503")
    assert "does not mean your films disappeared" in failed["body"]


def test_web_discovery_journey(evidence_db, tmp_path, monkeypatch):
    # Freeze assessment time so catalog validity remains deterministic in future CI.
    read = web.discovery_command
    monkeypatch.setattr(
        web, "discovery_command", lambda *args, **kwargs: read(*args, **kwargs, now=NOW)
    )
    app = prepare(evidence_db, tmp_path)
    inspect_browse(app)
    inspect_evidence(app)
    inspect_aliases(app)
    inspect_offer_identity(app, monkeypatch)
    inspect_personal(app, tmp_path)
    inspect_dispositions(app, evidence_db, tmp_path)
    inspect_movary(app, tmp_path, monkeypatch)
    # Exercise the same WSGI boundary for assets and health, not an internal renderer.
    assert request(app, "/style.css")["headers"]["Content-Type"].startswith("text/css")
    assert request(app, "/health")["status"] == "200 OK"
    assert request(app, "/films/999")["status"].startswith("404")
    inspect_missing(app, evidence_db, tmp_path)
