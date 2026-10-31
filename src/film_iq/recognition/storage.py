"""Per-revision declarations and explicitly reviewed legacy classifications."""

import json
import sqlite3
from dataclasses import asdict

from film_iq.ingest.persist import _savepoint
from film_iq.recognition.models import AwardOutcome, ReceptionMetric, Selection
from film_iq.recognition.review import ClassificationReview

Component = Selection | AwardOutcome | ReceptionMetric


def encode(value) -> str:
    return json.dumps(asdict(value), sort_keys=True, ensure_ascii=False, default=str)


def declare_selection(db, entry: str, revision: str, selection: Selection) -> None:
    """A manifest declares its type before the independent extraction audit."""
    _record(db, entry, revision, selection, None)


def classify_entry(
    db: sqlite3.Connection,
    entry: str,
    revision: str,
    component: Component | tuple[Component, ...],
    review: ClassificationReview,
) -> None:
    """Only a reviewed initial unknown classification can supplement legacy evidence.

    Known classifications are immutable. Corrections need a new pending extraction
    revision and its independent acceptance; current accepted facts stay intact.
    """
    if type(review) is not ClassificationReview:
        raise ValueError("an explicit independent classification review is required")
    _record(db, entry, revision, component, encode(review))


def _record(db, entry, revision, component, review):
    kind, payload = _payload(component)
    row = db.execute(
        "SELECT kind,payload,review FROM entry_recognition WHERE entry_id=? AND revision_id=?",
        (entry, revision),
    ).fetchone()
    if _existing(row, kind, payload, review):
        return
    if review is None and db.execute(
        "SELECT acceptance_state FROM extraction_revision WHERE id=?", (revision,)
    ).fetchone() != ("pending",):
        raise ValueError("accepted legacy evidence requires an explicit classification review")
    with _savepoint(db):
        db.execute(
            "INSERT INTO entry_recognition VALUES (?,?,?,?,?) ON CONFLICT(entry_id,revision_id) "
            "DO UPDATE SET kind=excluded.kind,payload=excluded.payload,review=excluded.review",
            (entry, revision, kind, payload, review),
        )


def _existing(row, kind, payload, review):
    if row is None:
        return False
    if row[:2] == (kind, payload):
        return review is None or row[2] is not None
    if row[0] != "unknown" or row[2] is not None or review is None:
        raise ValueError("classification differs; create and independently accept a new revision")
    return False


def _payload(component):
    items = component if type(component) is tuple else (component,)
    if not items or any(
        type(item) not in {Selection, AwardOutcome, ReceptionMetric} for item in items
    ):
        raise ValueError("supported typed recognition components are required")
    kinds = {item.kind for item in items}
    if len(kinds) != 1:
        raise ValueError("one source entry must declare one evidence kind")
    return items[0].kind, "[" + ",".join(sorted({encode(item) for item in items})) + "]"
