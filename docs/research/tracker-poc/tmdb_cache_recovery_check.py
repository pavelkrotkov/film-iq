"""Exercise a fictional cache's copy inventory, expiry and offline recovery.

All files are synthetic and created under the ignored project-local POC cache.
This check does not read provider credentials, live data, or existing backups.
"""

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tmdb_cache import (
    CACHE_ID,
    initialize_authority,
    purge_due,
    read_film,
    record_policy,
    write_film,
)

from film_iq.cache_purge import purge
from film_iq.retention import CachePolicy

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / ".cache/tracker-poc"
OBSERVED = datetime(2026, 1, 1, tzinfo=UTC)
DEADLINE = OBSERVED + timedelta(days=30)
POLICY = CachePolicy(
    source="TMDB",
    allowed=True,
    rights_evidence="Fictional test permission only",
    attribution="Fictional test attribution",
    expires_at=DEADLINE,
)
FILM: dict[str, Any] = {
    "tmdb_id": 42,
    "title": "Fictional film",
    "original_title": "Fictional original",
    "synopsis": "A fictional synopsis.",
    "year": 2001,
    "genres": ["Fiction"],
    "directors": ["Fictional director"],
    "poster_url": "https://image.tmdb.org/t/p/w500/fictional.jpg",
    "imdb_title_url": None,
    "availability": {
        "status": "complete",
        "checked_at": OBSERVED.isoformat(),
        "provider_url": None,
        "offers": [{"provider": "Fictional stream", "kind": "subscription"}],
    },
}


def verify_restored(root: Path, authority: Path) -> None:
    if not root.resolve().is_relative_to(FIXTURES.resolve()):
        raise ValueError("Expected a project-local fictional fixture")
    renewed = replace(POLICY, expires_at=OBSERVED + timedelta(days=120))
    record = read_film(root, renewed, 42, OBSERVED + timedelta(days=1), authority=authority)
    assert record is not None
    assert record["metadata"]["data"]["synopsis"] == FILM["synopsis"]
    assert record["availability"]["data"]["offers"] == FILM["availability"]["offers"]
    assert record["metadata"]["expires_at"] == DEADLINE.isoformat()
    assert record["availability"]["expires_at"] == DEADLINE.isoformat()
    assert read_film(root, renewed, 42, DEADLINE, authority=authority) is None


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True, mode=0o700)
    fixture = Path(tempfile.mkdtemp(prefix="fictional-cache-recovery-", dir=FIXTURES))
    source, extracted, restored = (fixture / name for name in ("source", "extracted", "restored"))
    for directory in (source, extracted, restored):
        directory.mkdir(mode=0o700)
    authority = fixture / "authority.json"
    initialize_authority(source, authority, POLICY, OBSERVED)
    write_film(source, POLICY, FILM, OBSERVED, OBSERVED, authority=authority)
    fictional_cache_bytes = (source / "42.json").read_bytes()
    fictional_marker = (source / CACHE_ID).read_bytes()
    backup = fixture / "fictional-backup.tar.gz"
    with tarfile.open(backup, "w:gz") as archive:
        archive.add(source / "42.json", arcname="42.json")
        archive.add(source / CACHE_ID, arcname=CACHE_ID)
    os.chmod(backup, 0o600)
    with tarfile.open(backup, "r:gz") as archive:
        member = archive.extractfile("42.json")
        assert member is not None
        (extracted / "42.json").write_bytes(member.read())
        marker = archive.extractfile(CACHE_ID)
        assert marker is not None
        (extracted / CACHE_ID).write_bytes(marker.read())
    shutil.copyfile(extracted / "42.json", restored / "42.json")
    shutil.copyfile(extracted / CACHE_ID, restored / CACHE_ID)
    for directory in (extracted, restored):
        (directory / "42.json").chmod(0o600)

    renewed = replace(POLICY, expires_at=OBSERVED + timedelta(days=120))
    record_policy(authority, renewed, OBSERVED + timedelta(days=1))
    # A fresh interpreter reads the restored record with the separate authority.
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--verify-restored",
            str(restored),
            str(authority),
        ],
        capture_output=True,
        check=False,
        timeout=15,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if result.returncode:
        raise RuntimeError("Fresh-process fictional restore verification failed")

    # Renewing a policy and replaying the identical observation before expiry
    # cannot give the already-retained facts a later deadline.
    write_film(restored, renewed, FILM, OBSERVED, OBSERVED + timedelta(days=1), authority=authority)
    verify_restored(restored, authority)

    inventory = (
        "source/42.json",
        "fictional-backup.tar.gz",
        "extracted/42.json",
        "restored/42.json",
    )
    sentinel = fixture / "unrelated-fictional-file.txt"
    sentinel.write_text("unrelated fixture", encoding="utf-8")
    assert purge(fixture, list(inventory), POLICY, DEADLINE - timedelta(seconds=1)) == ()
    assert purge(fixture, list(inventory), POLICY, DEADLINE) == inventory
    assert all((fixture / name).is_file() for name in inventory)
    actions = purge_due(source, renewed, DEADLINE, authority=authority)
    assert actions == (("42.json", ("metadata", "availability")),)
    assert (source / "42.json").is_file(), "Preview must not delete the source fixture"
    assert purge_due(source, renewed, DEADLINE, authority=authority, execute=True) == actions
    assert purge(fixture, list(inventory), POLICY, DEADLINE, execute=True) == inventory
    assert all(not (fixture / name).exists() for name in inventory)
    assert sentinel.read_text(encoding="utf-8") == "unrelated fixture"
    try:
        write_film(
            source, renewed, FILM, OBSERVED, DEADLINE + timedelta(seconds=1), authority=authority
        )
    except (ValueError, PermissionError):
        pass
    else:
        raise AssertionError("An already-purged observation was replayed under a later policy")
    assert not (source / "42.json").exists()

    # A restored older copy must use the latest independently held authority.
    older_restore = fixture / "older-restore-without-watermark"
    older_restore.mkdir(mode=0o700)
    (older_restore / CACHE_ID).write_bytes(fictional_marker)
    (older_restore / "42.json").write_bytes(fictional_cache_bytes)
    assert (
        read_film(older_restore, renewed, 42, DEADLINE + timedelta(seconds=1), authority=authority)
        is None
    )
    try:
        write_film(
            older_restore,
            renewed,
            FILM,
            OBSERVED,
            DEADLINE + timedelta(seconds=1),
            authority=authority,
        )
    except (ValueError, PermissionError):
        pass
    else:
        raise AssertionError("A restored old observation was replayed")
    assert purge_due(
        older_restore, renewed, DEADLINE + timedelta(seconds=1), authority=authority, execute=True
    )
    assert not (older_restore / "42.json").exists()

    # A shorter decision remains binding after a later renewal, even if no
    # cache read or purge occurred while the shorter policy was active.
    shortened_root, shortened_authority = (
        fixture / "shortened",
        fixture / "shortened-authority.json",
    )
    initialize_authority(shortened_root, shortened_authority, renewed, OBSERVED)
    write_film(shortened_root, renewed, FILM, OBSERVED, OBSERVED, authority=shortened_authority)
    record_policy(shortened_authority, POLICY, OBSERVED + timedelta(days=10))
    record_policy(shortened_authority, renewed, OBSERVED + timedelta(days=20))
    before_expiry = read_film(
        shortened_root, renewed, 42, OBSERVED + timedelta(days=20), authority=shortened_authority
    )
    assert (
        before_expiry is not None
        and before_expiry["metadata"]["expires_at"] == DEADLINE.isoformat()
    )
    assert (
        read_film(
            shortened_root,
            renewed,
            42,
            DEADLINE + timedelta(seconds=1),
            authority=shortened_authority,
        )
        is None
    )
    assert purge_due(
        shortened_root,
        renewed,
        DEADLINE + timedelta(seconds=1),
        authority=shortened_authority,
        execute=True,
    )

    # A delayed write keeps the policy provenance of each observation rather
    # than attributing earlier source data to the most recent decision.
    provenance_root, provenance_authority = (
        fixture / "provenance",
        fixture / "provenance-authority.json",
    )
    initial = replace(
        renewed,
        rights_evidence="Fictional original rights",
        attribution="Fictional original attribution",
        version="fictional-a",
    )
    changed = replace(
        POLICY,
        rights_evidence="Fictional revised rights",
        attribution="Fictional revised attribution",
        version="fictional-b",
    )
    initialize_authority(provenance_root, provenance_authority, initial, OBSERVED)
    record_policy(provenance_authority, changed, OBSERVED + timedelta(days=2))
    delayed = {
        **FILM,
        "availability": {
            **FILM["availability"],
            "checked_at": (OBSERVED + timedelta(days=1)).isoformat(),
        },
    }
    write_film(
        provenance_root,
        changed,
        delayed,
        OBSERVED,
        OBSERVED + timedelta(days=3),
        authority=provenance_authority,
    )
    actual = read_film(
        provenance_root, changed, 42, OBSERVED + timedelta(days=3), authority=provenance_authority
    )
    assert actual is not None
    for section in (actual["metadata"], actual["availability"]):
        assert section["policy_version"] == "fictional-a"
        assert section["rights_evidence"] == "Fictional original rights"
        assert section["attribution"] == "Fictional original attribution"
        assert section["expires_at"] == DEADLINE.isoformat()

    # Under source termination, a corrupt managed record must be explicitly
    # previewed and removed without blocking other managed records. The policy
    # history prevents its original observations from being replayed later.
    corrupt_root, corrupt_authority = fixture / "corrupt", fixture / "corrupt-authority.json"
    initialize_authority(corrupt_root, corrupt_authority, initial, OBSERVED)
    write_film(corrupt_root, initial, FILM, OBSERVED, OBSERVED, authority=corrupt_authority)
    (corrupt_root / "43.json").write_text("{invalid fictional fixture", encoding="utf-8")
    unaffected = corrupt_root / "unrelated.txt"
    unaffected.write_text("preserve", encoding="utf-8")
    corrupt_terminated = replace(initial, terminated=True)
    termination_time = OBSERVED + timedelta(days=1)
    record_policy(corrupt_authority, corrupt_terminated, termination_time)
    expected = (("42.json", ("metadata", "availability")), ("43.json", ("corrupt",)))
    assert (
        purge_due(corrupt_root, corrupt_terminated, termination_time, authority=corrupt_authority)
        == expected
    )
    assert (corrupt_root / "42.json").exists() and (corrupt_root / "43.json").exists()
    assert (
        purge_due(
            corrupt_root,
            corrupt_terminated,
            termination_time,
            authority=corrupt_authority,
            execute=True,
        )
        == expected
    )
    assert not (corrupt_root / "42.json").exists() and not (corrupt_root / "43.json").exists()
    assert unaffected.read_text(encoding="utf-8") == "preserve"
    record_policy(corrupt_authority, initial, termination_time + timedelta(seconds=1))
    try:
        write_film(
            corrupt_root,
            initial,
            FILM,
            OBSERVED,
            termination_time + timedelta(seconds=1),
            authority=corrupt_authority,
        )
    except (ValueError, PermissionError):
        pass
    else:
        raise AssertionError("Source termination must prevent old observation replay")

    # Under an active renewed policy, corruption is not proof that its own
    # contents are expired; it must not block cleanup of another expired film.
    active_root, active_authority = fixture / "active-corrupt", fixture / "active-authority.json"
    initialize_authority(active_root, active_authority, POLICY, OBSERVED)
    write_film(active_root, POLICY, FILM, OBSERVED, OBSERVED, authority=active_authority)
    record_policy(active_authority, renewed, OBSERVED + timedelta(days=1))
    broken = active_root / "43.json"
    broken.write_text("{fictional corruption", encoding="utf-8")
    expected = (("42.json", ("metadata", "availability")), ("43.json", ("corrupt_unresolved",)))
    after_deadline = DEADLINE + timedelta(seconds=1)
    assert purge_due(active_root, renewed, after_deadline, authority=active_authority) == expected
    assert (active_root / "42.json").exists() and broken.exists()
    assert (
        purge_due(active_root, renewed, after_deadline, authority=active_authority, execute=True)
        == expected
    )
    assert not (active_root / "42.json").exists()
    assert broken.read_text(encoding="utf-8") == "{fictional corruption"

    # A missing or mismatched authority never creates a replacement implicitly.
    try:
        read_film(restored, renewed, 42, DEADLINE, authority=fixture / "missing-authority.json")
    except ValueError:
        pass
    else:
        raise AssertionError("Missing authority must fail closed")
    try:
        read_film(restored, renewed, 42, DEADLINE, authority=shortened_authority)
    except ValueError:
        pass
    else:
        raise AssertionError("An unrelated authority must fail closed")

    terminated = replace(POLICY, terminated=True)
    (fixture / "termination-fixture.json").write_bytes(fictional_cache_bytes)
    assert purge(fixture, ["termination-fixture.json"], terminated, OBSERVED) == (
        "termination-fixture.json",
    )
    assert purge(fixture, ["termination-fixture.json"], terminated, OBSERVED, execute=True) == (
        "termination-fixture.json",
    )
    assert not (fixture / "termination-fixture.json").exists()
    assert sentinel.exists()
    print("Fictional retained-authority recovery, policy shortening and named-copy purge passed")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--verify-restored":
        verify_restored(Path(sys.argv[2]), Path(sys.argv[3]))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("Invalid arguments")
