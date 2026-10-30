"""Bounded supported exports and mode-0600 atomic private JSON publication."""

import json
import os
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path


def _export(command: list[str], path: Path, read: Callable[[Path], list[dict]]) -> list[dict]:
    """Full argv must emit CSV only to stdout (Movary php://stdout --silent)."""
    with path.open("wb") as output:
        subprocess.run(command, stdout=output, stderr=subprocess.DEVNULL, check=True, timeout=300)
    return read(path)


def private_json(path: Path, value: dict) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, delete=False, encoding="utf-8"
    ) as output:
        pending = Path(output.name)
        try:
            json.dump(value, output, ensure_ascii=False)
            output.flush()
            os.fsync(output.fileno())
            os.replace(pending, path)
        finally:
            pending.unlink(missing_ok=True)


def rows(
    path: Path | None, command: list[str] | None, target: Path, reader: Callable[[Path], list[dict]]
) -> list[dict]:
    if (path is None) == (command is None):
        raise ValueError("Supply exactly one complete CSV or export command for each export")
    return reader(path) if path is not None else _export(command or [], target, reader)
