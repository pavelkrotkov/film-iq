"""Shared WSGI browser adapter and accepted fixture for the integrated web journey."""

import json
from dataclasses import replace
from io import BytesIO
from urllib.parse import urlsplit

from discovery_fixtures import accept_source, cohort
from discovery_offer_support import observation
from display_fixtures import catalog_path
from recognition_support import REVIEW
from test_discovery_batch import selection

from film_iq import web
from film_iq.availability.codec import encode
from film_iq.recognition.models import AwardOutcome
from film_iq.recognition.storage import classify_entry


def request(app, url="/", method="GET", body=""):
    response: dict = {}
    parts = urlsplit(url)
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": parts.path,
        "QUERY_STRING": parts.query,
        "wsgi.input": BytesIO(body.encode()),
        "CONTENT_LENGTH": str(len(body.encode())),
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
    }

    def start(status, headers):
        response.update(status=status, headers=dict(headers))

    response["body"] = b"".join(app(environ, start)).decode()
    return response


def prepare(db, root):
    # Use the actual accepted DB/read pipeline, including adversarial source text.
    accept_source(db)
    db.execute(
        "UPDATE entry_observation SET raw_title=?,director='Source Director',tie='group-a'",
        ("A <script>alert(1)</script> Film",),
    )
    award = AwardOutcome(
        "Fixture festival",
        "2025",
        "Performance",
        "prize",
        recipient="Fixture Actor",
        recipient_kind="person",
    )
    classify_entry(db, "entry", "rev", award, REVIEW)
    second = selection(db, "selected-alias")
    supplemental = selection(db, "supplemental-critic")
    db.executemany(
        "UPDATE entry_observation SET raw_title=?,director=? WHERE revision_id=?",
        [
            ("Other source alias", "Other source director", second["revision_id"]),
            (
                "Supplemental source alias",
                "Supplemental source director",
                supplemental["revision_id"],
            ),
        ],
    )
    db.executemany(
        "UPDATE source_document SET url=? WHERE id=(SELECT document_id FROM extraction_revision WHERE id=?)",
        [
            ("https://example.test/second-source", second["revision_id"]),
            ("https://example.test/supplemental-source", supplemental["revision_id"]),
        ],
    )
    db.execute(
        "UPDATE entry_observation SET rank=NULL,tie=NULL WHERE revision_id=?",
        (supplemental["revision_id"],),
    )
    db.execute(
        "UPDATE published_list SET rank_semantics='unranked' WHERE id=(SELECT list_id FROM extraction_revision WHERE id=?)",
        (supplemental["revision_id"],),
    )
    db.commit()
    selected = root / "cohort.json"
    selected.write_text(json.dumps(cohort()))
    other = root / "second-cohort.json"
    other.write_text(json.dumps(second))
    return web.Application(root / "evidence.db", [selected, other], catalog=catalog_path(root))


def inspect_offer_identity(app, monkeypatch):
    # A reviewed prior report cannot lend film certainty to an unreviewed attempt.
    prior = json.loads(encode(observation()))
    latest = json.loads(encode(replace(observation(1), work_reviewed=False)))
    latest["assertions"][0]["url"] = "https://example.test/unreviewed-film"
    report = app.report()
    report["candidates"][0]["offer_states"] = [
        {"current": prior, "latest_attempt": latest, "attribution": "Synthetic source credit"}
    ]
    with monkeypatch.context() as patch:
        patch.setattr(app, "report", lambda: report)
        page = request(app, "/films/123")["body"]
    assert 'href="https://example.test/film"' in page
    assert 'href="https://example.test/unreviewed-film"' not in page
    assert "No reviewed viewing links supplied" in page


def inspect_aliases(app):
    assert "1 film to explore" in request(app, "/?q=Other+source+director")["body"]
    assert "1 film to explore" in request(app, "/?q=Supplemental+source+alias")["body"]
    page = request(app, "/films/123")["body"]
    assert page.count('href="https://example.test/supplemental-source"') == 1
    assert page.count('href="https://example.test/second-source"') == 1
    assert "Supplemental source director" in page
    assert "Classification reviewed" in page
    assert "Unranked selection" in page
