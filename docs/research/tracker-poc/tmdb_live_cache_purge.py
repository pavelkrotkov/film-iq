"""Preview or purge one offline live-cache directory after stopping its writer."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from tmdb_cache import purge_due
from tmdb_live_cache import policy_file

from film_iq.retention import status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument(
        "--writers-stopped",
        action="store_true",
        help="assert the bridge and every other writer are stopped",
    )
    parser.add_argument("--execute", action="store_true", help="purge instead of previewing")
    args = parser.parse_args()
    if not args.writers_stopped:
        parser.error("Stop every writer before preview or execution, then pass --writers-stopped")
    if not args.directory.is_absolute() or not args.directory.is_dir():
        parser.error("Expected an existing absolute cache directory")
    try:
        policy = policy_file(args.directory)
        now = datetime.now(UTC)
        if status(policy, now) == "blocked":
            print("Cache policy is blocked; no purge decision is available.")
            return 1
        actions = purge_due(
            args.directory / "cache",
            policy,
            now,
            authority=args.directory / "authority.json",
            execute=args.execute,
        )
    except (OSError, ValueError, TypeError, KeyError):
        print("Cache purge unavailable; inspect the local policy and authority.")
        return 1
    unresolved = sum(sections == ("corrupt_unresolved",) for _, sections in actions)
    affected = [sections for _, sections in actions if sections != ("corrupt_unresolved",)]
    print(
        f"{'Purged' if args.execute else 'Would purge'}: {len(affected)} records; {sum(len(sections) for sections in affected)} sections; unresolved: {unresolved}."
    )
    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
