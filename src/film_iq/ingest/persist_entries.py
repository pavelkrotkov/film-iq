"""Persist validated entry observations for a new revision."""

import sqlite3

from film_iq.domain import Observation
from film_iq.ingest.adapters import film_registry, nbr_2023, page_capture
from film_iq.ingest.persist_checks import SourcePolicy, _key


def _observations(
    extraction: nbr_2023.Extraction | film_registry.Extraction | page_capture.Extraction,
    policy: SourcePolicy,
    list_id: str,
    revision_id: str,
    run_id: str,
) -> list[Observation]:
    observations = []
    for entry in extraction.entries:
        context = (
            f"{entry.title} ({entry.release_date})"
            if isinstance(entry, film_registry.Entry)
            else entry.raw_context
        )
        observations.append(
            Observation(
                policy.id,
                list_id,
                _key(list_id, str(entry.position)),
                run_id,
                revision_id,
                entry.title,
                context,
                entry.locator,
                entry.rank,
                tie=getattr(entry, "tie", None),
                position=entry.position,
            )
        )
    return observations


def _store_entries(db: sqlite3.Connection, observations: list[Observation]) -> None:
    for entry in observations:
        db.execute(
            "INSERT INTO list_entry VALUES (?,?,?,?) ON CONFLICT(id) DO NOTHING",
            (entry.entry_id, entry.source_id, entry.edition_id, str(entry.position)),
        )
        stored = db.execute(
            "SELECT source_id,list_id,entry_key FROM list_entry WHERE id=?", (entry.entry_id,)
        ).fetchone()
        if stored != (entry.source_id, entry.edition_id, str(entry.position)):
            raise ValueError("list entry conflicts with existing evidence")
        db.execute(
            "INSERT INTO entry_observation (entry_id,source_id,list_id,revision_id,raw_title,raw_context,position,rank,tie,locator,extraction_decision) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                entry.entry_id,
                entry.source_id,
                entry.edition_id,
                entry.revision_id,
                entry.raw_title,
                entry.raw_context,
                entry.position,
                entry.rank,
                entry.tie,
                entry.locator,
                entry.extraction_decision,
            ),
        )
