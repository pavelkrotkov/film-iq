"""Shared WSGI browser adapter and accepted fixture for the integrated web journey."""

import json
from io import BytesIO
from urllib.parse import urlsplit

from discovery_fixtures import accept_source, cohort
from display_fixtures import catalog_path
from recognition_support import REVIEW

from film_iq import web
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
    db.commit()
    selected = root / "cohort.json"
    selected.write_text(json.dumps(cohort()))
    return web.Application(root / "evidence.db", [selected], catalog=catalog_path(root))
