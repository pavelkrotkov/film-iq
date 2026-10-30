"""Atomically replace a private complete Movary snapshot, or retain stale state."""

import csv
import subprocess
import tempfile
from http.client import HTTPException
from pathlib import Path
from typing import Any

from film_iq.history_csv import read_history
from film_iq.movary import MovaryClient, read_ratings
from film_iq.personal_io import private_json, rows
from film_iq.personal_snapshot import build_snapshot


def refresh(
    client: MovaryClient,
    snapshot: Path,
    *,
    ratings_csv: Path | None = None,
    history_csv: Path | None = None,
    ratings_command: list[str] | None = None,
    history_command: list[str] | None = None,
) -> dict[str, Any]:
    """Stage all three API collections and both exports before replacing anything.

    Explicit CSV inputs are an operator-asserted complete-export/manual fallback.
    A fresh exporter command is preferred. Errors are reported without private
    payloads; last successful state is retained and the attempt is marked stale.
    """
    snapshot.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with tempfile.TemporaryDirectory(dir=snapshot.parent, prefix=".refresh-") as directory:
            collections = {name: client.read(name) for name in ("played", "history", "watchlist")}
            ratings = rows(
                ratings_csv, ratings_command, Path(directory) / "ratings.csv", read_ratings
            )
            history = rows(
                history_csv, history_command, Path(directory) / "history.csv", read_history
            )
            result = build_snapshot(collections, ratings, history)
            private_json(snapshot, result)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        csv.Error,
        HTTPException,
        subprocess.SubprocessError,
    ):
        private_json(
            snapshot.with_suffix(snapshot.suffix + ".status"),
            {"stale": True, "error": "refresh_failed"},
        )
        raise ValueError("Movary refresh failed; prior snapshot retained and stale") from None
    private_json(
        snapshot.with_suffix(snapshot.suffix + ".status"),
        {"stale": False, "last_successful_refresh": result["last_successful_refresh"]},
    )
    return result
