"""Preview or renew one stopped bridge's local cache policy."""

import argparse
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tmdb_cache import _bound_authority, record_policy
from tmdb_live_cache import policy_file

from film_iq.personal_io import private_json

ROOT = Path(__file__).resolve().parents[3]


def renew(
    directory: Path, days: int, now: datetime, *, execute: bool = False
) -> tuple[datetime, datetime]:
    """Extend a permitted, nonterminated policy without changing old observations."""
    if (
        not directory.is_absolute()
        or not directory.is_dir()
        or not directory.resolve().is_relative_to(ROOT)
    ):
        raise ValueError("Expected an existing project-local absolute cache directory")
    if type(days) is not int or not 1 <= days <= 30 or now.utcoffset() is None:
        raise ValueError("Expected a timezone-aware time and between 1 and 30 days")
    now = now.astimezone(UTC)
    policy = policy_file(directory)
    if not policy.allowed or policy.terminated:
        raise PermissionError("A blocked or terminated policy cannot be renewed")
    root, authority = directory / "cache", directory / "authority.json"
    _bound_authority(root, authority, policy, now)
    updated = replace(policy, expires_at=now + timedelta(days=days))
    if updated.expires_at <= policy.expires_at:
        raise ValueError("The new deadline must extend the existing policy")
    if execute:
        record_policy(authority, updated, now)
        payload = asdict(updated)
        payload["expires_at"] = updated.expires_at.isoformat()
        private_json(directory / "policy.json", payload)
        _bound_authority(root, authority, updated, now)
    return policy.expires_at, updated.expires_at


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument(
        "--days", required=True, type=int, help="new policy window, at most 30 days"
    )
    parser.add_argument(
        "--writers-stopped",
        action="store_true",
        help="assert every writer for this cache is stopped",
    )
    parser.add_argument(
        "--execute", action="store_true", help="record the renewal instead of previewing"
    )
    args = parser.parse_args()
    if not args.writers_stopped:
        parser.error("Stop every writer first, then pass --writers-stopped")
    try:
        old, new = renew(args.directory, args.days, datetime.now(UTC), execute=args.execute)
    except (OSError, ValueError, TypeError, KeyError, PermissionError):
        print(
            "Renewal unavailable. Keep the bridge stopped; the policy and authority may require review."
        )
        return 1
    verb = "Renewed" if args.execute else "Would renew"
    print(
        f"{verb} the policy from {old.isoformat()} to {new.isoformat()}; existing observation deadlines do not extend."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
