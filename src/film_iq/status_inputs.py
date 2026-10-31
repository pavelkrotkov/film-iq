"""Allowlisted file status; private contents and diagnostic exceptions stay hidden."""

import sqlite3
from datetime import datetime
from pathlib import Path

from film_iq.display_catalog import read_catalog


def inspect_input(path: Path | None, reader, now: datetime) -> dict:
    if path is None:
        return {"state": "not_configured"}
    try:
        return reader(path, now)
    except FileNotFoundError:
        return {"state": "missing"}
    except (OSError, ValueError, KeyError, TypeError, AttributeError, sqlite3.Error):
        return {"state": "invalid"}


def catalog_status(path: Path, now: datetime) -> dict:
    _, context = read_catalog(path, now)
    return {key: context[key] for key in ("observed_at", "expires_at")} | {
        "state": context["status"]
    }
