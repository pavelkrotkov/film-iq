"""Preview or explicitly delete only named disposable cache files."""

from datetime import datetime
from pathlib import Path

from film_iq.retention import CachePolicy, status


def purge(
    root: Path, names: list[str], policy: CachePolicy, now: datetime, *, execute: bool = False
) -> tuple[str, ...]:
    """Preview named disposable cache files; explicit execution never scans source data."""
    paths = [(root / name).resolve() for name in names]
    if any(not path.is_relative_to(root.resolve()) for path in paths):
        raise ValueError("cache names must stay inside the supplied cache root")
    if status(policy, now) != "purge_due":
        return ()
    if execute:
        for path in paths:
            path.unlink(missing_ok=True)
    return tuple(names)
