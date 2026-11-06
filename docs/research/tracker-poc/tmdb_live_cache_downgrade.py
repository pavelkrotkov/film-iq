"""Remove unknown availability sections before rolling back to an older reader.

Stop every writer first. This does not touch tracker records or the authority.
"""

import argparse
from pathlib import Path

from tmdb_cache import _load, _save, inventory

ROOT = Path(__file__).resolve().parents[3]


def downgrade(root: Path, *, execute: bool = False) -> int:
    """Preview or remove only validated unknown sections from an offline cache."""
    if (
        not root.is_absolute()
        or not root.is_dir()
        or root.is_symlink()
        or not root.resolve().is_relative_to(ROOT)
    ):
        raise ValueError("An existing project-local absolute cache directory is required")
    affected = []
    for name in inventory(root):
        if name.endswith(".tmp"):
            raise ValueError("Unresolved temporary cache file")
        path = root / name
        record = _load(path, int(name[:-5]))
        section = record["availability"]
        if section and section["data"]["status"] == "unknown":
            affected.append((path, record))
    if execute:
        for path, record in affected:
            record["availability"] = None
            _save(path, record)
    return len(affected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path, help="live cache parent directory")
    parser.add_argument("--writers-stopped", action="store_true")
    parser.add_argument("--execute", action="store_true", help="apply instead of preview")
    args = parser.parse_args()
    if not args.writers_stopped:
        parser.error("Stop every writer before preview or execution, then pass --writers-stopped")
    try:
        count = downgrade(args.directory / "cache", execute=args.execute)
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        print("Downgrade unavailable; inspect the offline cache before rollback.")
        return 1
    print(
        f"{'Removed' if args.execute else 'Would remove'} unknown availability sections: {count}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
