"""Synthetic source selections and private ledger inputs, with no personal scores."""

import json
from dataclasses import replace
from pathlib import Path

from discovery_fixtures import accept_source, cohort, fresh_status, snapshot
from offer_store_support import NOW, fetch

from film_iq.availability.codec import encode, timestamp
from film_iq.availability.store_command import main
from film_iq.discovery_command import discovery_command


def configure(db, root: Path):
    accept_source(db)
    db.commit()
    personal = snapshot()
    personal["films"][0].update(
        personal_enjoyment=None, personal_artistic_merit=None, merit_status="unknown"
    )
    (root / "cohort.json").write_text(json.dumps(cohort()))
    (root / "personal.json").write_text(json.dumps(personal))
    (root / "personal.json.status").write_text(json.dumps(fresh_status()))


def observation(day=0, **kwargs):
    item = fetch(day, **kwargs)
    assertions = tuple(
        replace(a, opportunity=replace(a.opportunity, film_id=123)) for a in item.assertions
    )
    return replace(item, film_id=123, assertions=assertions)


def import_observation(root: Path, item):
    path = root / "offer.json"
    path.write_text(encode(item))
    return main(
        [
            "import",
            "--database",
            str(root / "evidence.db"),
            "--input",
            str(path),
            "--now",
            timestamp(item.checked_at),
        ]
    )


def report(root: Path, now=NOW, output_format="json"):
    value = discovery_command(
        root / "cohort.json", root / "personal.json", root / "evidence.db", output_format, now=now
    )
    return json.loads(value) if output_format == "json" else value
