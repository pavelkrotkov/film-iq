"""Atomically publish a mode-0600 private report."""

import os
import tempfile
from pathlib import Path


def private_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, delete=False, encoding="utf-8"
    ) as file:
        pending = Path(file.name)
        try:
            file.write(value)
            file.flush()
            os.fsync(file.fileno())
            os.replace(pending, path)
        finally:
            pending.unlink(missing_ok=True)
