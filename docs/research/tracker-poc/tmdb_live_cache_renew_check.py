"""Exercise offline cache-policy renewal with fictional records only."""

import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from tmdb_cache import (
    _bound_authority,
    initialize_authority,
    purge_due,
    read_film,
    record_policy,
    write_film,
)
from tmdb_live_cache import policy_file
from tmdb_live_cache_renew import renew

from film_iq.retention import CachePolicy

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 1, 3, tzinfo=UTC)
POLICY = CachePolicy(
    "TMDB", True, "Fictional permission", "Fictional attribution", NOW + timedelta(days=3)
)
FILM_ID = 987654321
FILM = {
    "tmdb_id": FILM_ID,
    "title": "Fictional film",
    "availability": {"status": "complete", "checked_at": NOW.isoformat(), "offers": []},
}


def fixture(directory: Path) -> tuple[Path, Path]:
    directory.mkdir()
    root, authority = directory / "cache", directory / "authority.json"
    initialize_authority(root, authority, POLICY, NOW - timedelta(days=1))
    (directory / "policy.json").write_text(
        json.dumps({**asdict(POLICY), "expires_at": POLICY.expires_at.isoformat()})
    )
    write_film(root, POLICY, FILM, NOW, NOW, authority=authority, max_age=timedelta(days=7))
    return root, authority


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="fictional-renewal-", dir=ROOT / ".cache/tracker-poc"
    ) as place:
        try:
            renew(Path("/"), 30, NOW, execute=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Renewal allowed a non-project directory")
        base = Path(place)
        directory = base / "normal"
        root, authority = fixture(directory)
        original = read_film(root, POLICY, FILM_ID, NOW, authority=authority)
        assert original is not None
        prior = (directory / "policy.json").read_bytes(), authority.read_bytes()
        old, proposed = renew(directory, 30, NOW + timedelta(seconds=1))
        assert old == POLICY.expires_at and proposed == NOW + timedelta(days=30, seconds=1)
        assert prior == ((directory / "policy.json").read_bytes(), authority.read_bytes())
        renew(directory, 30, NOW + timedelta(seconds=1), execute=True)
        updated = policy_file(directory)
        retained = read_film(
            root, updated, FILM_ID, NOW + timedelta(seconds=2), authority=authority
        )
        assert retained is not None
        for section in ("metadata", "availability"):
            assert retained[section]["expires_at"] == original[section]["expires_at"]
        assert read_film(root, updated, FILM_ID, POLICY.expires_at, authority=authority) is None
        fresh_time = POLICY.expires_at + timedelta(seconds=1)
        fresh = {
            **FILM,
            "availability": {
                "status": "complete",
                "checked_at": fresh_time.isoformat(),
                "offers": [],
            },
        }
        purge_due(root, updated, fresh_time, authority=authority, execute=True)
        write_film(
            root,
            updated,
            fresh,
            fresh_time,
            fresh_time,
            authority=authority,
            max_age=timedelta(days=7),
        )
        renewed_observation = read_film(root, updated, FILM_ID, fresh_time, authority=authority)
        assert renewed_observation is not None
        assert datetime.fromisoformat(
            renewed_observation["metadata"]["expires_at"]
        ) == fresh_time + timedelta(days=7)

        expired = base / "expired"
        expired_root, expired_authority = fixture(expired)
        after_expiry = POLICY.expires_at + timedelta(seconds=1)
        renew(expired, 30, after_expiry, execute=True)
        assert (
            read_film(
                expired_root,
                policy_file(expired),
                FILM_ID,
                after_expiry,
                authority=expired_authority,
            )
            is None
        )

        partial = base / "partial"
        partial_root, partial_authority = fixture(partial)
        with patch("tmdb_live_cache_renew.private_json", side_effect=OSError("fictional failure")):
            try:
                renew(partial, 30, NOW + timedelta(seconds=1), execute=True)
            except OSError:
                pass
            else:
                raise AssertionError("Partial update was accepted")
        try:
            _bound_authority(
                partial_root, partial_authority, policy_file(partial), NOW + timedelta(seconds=2)
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Mismatched policy and authority did not fail closed")

        blocked = base / "blocked"
        blocked_root, blocked_authority = fixture(blocked)
        denied = replace(POLICY, allowed=False)
        record_policy(blocked_authority, denied, NOW + timedelta(seconds=1))
        (blocked / "policy.json").write_text(
            json.dumps({**asdict(denied), "expires_at": denied.expires_at.isoformat()})
        )
        try:
            renew(blocked, 30, NOW + timedelta(seconds=2), execute=True)
        except PermissionError:
            pass
        else:
            raise AssertionError("Blocked policy was renewed")
        assert (blocked_root / "987654321.json").is_file()

        terminated = base / "terminated"
        terminated_root, terminated_authority = fixture(terminated)
        revoked = replace(POLICY, terminated=True)
        record_policy(terminated_authority, revoked, NOW + timedelta(seconds=1))
        (terminated / "policy.json").write_text(
            json.dumps({**asdict(revoked), "expires_at": revoked.expires_at.isoformat()})
        )
        try:
            renew(terminated, 30, NOW + timedelta(seconds=2), execute=True)
        except PermissionError:
            pass
        else:
            raise AssertionError("Terminated policy was renewed")
        assert (terminated_root / "987654321.json").is_file()

        command = [
            sys.executable,
            str(ROOT / "docs/research/tracker-poc/tmdb_live_cache_renew.py"),
            "--directory",
            str(directory),
            "--days",
            "30",
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        assert result.returncode != 0 and "987654321" not in result.stderr
        preview = subprocess.run(
            [*command, "--writers-stopped"], capture_output=True, text=True, timeout=15
        )
        assert preview.returncode == 0 and "Would renew" in preview.stdout
        assert "987654321" not in preview.stdout and str(directory) not in preview.stdout
    print("Fictional policy preview, renewal, deadlines and fail-closed checks passed")


if __name__ == "__main__":
    main()
