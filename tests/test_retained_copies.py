"""Named synthetic copies expire together; no live artifact discovery or cleanup."""

from dataclasses import replace

import pytest
from offer_store_support import EXPIRY, NOW, policy
from retained_copies_support import copied_deadline, copies

from film_iq.availability.policies import purge_source, record_policy
from film_iq.cache_purge import purge
from film_iq.retention import status


@pytest.mark.parametrize("terminated", [False, True], ids=["expiry", "termination"])
def test_explicit_inventory_purges_every_copy_but_preserves_unrelated(
    evidence_db, tmp_path, terminated
):
    identifier, unrelated, names, deadline = copies(evidence_db, tmp_path)
    inventory = {name: deadline for name in names}
    for name in ("online.sqlite", "isolated/online.sqlite", "restored.sqlite"):
        assert copied_deadline(tmp_path / name, identifier) == deadline
    sentinel = tmp_path / "user-owned.txt"
    sentinel.write_text("Unrelated user-owned sentinel")
    decision = replace(policy(allowed=True), terminated=terminated)
    now = NOW if terminated else EXPIRY
    record_policy(evidence_db, decision, now)
    assert status(decision, now) == "purge_due"
    assert purge(tmp_path, list(inventory), decision, now) == tuple(names)
    assert purge_source(evidence_db, "fixture", now) == (identifier,)
    assert all((tmp_path / name).exists() for name in names)
    assert copied_deadline(tmp_path / "online.sqlite", identifier) == deadline
    purge(tmp_path, list(inventory), decision, now, execute=True)
    purge_source(evidence_db, "fixture", now, execute=True)
    assert not any((tmp_path / name).exists() for name in names)
    assert evidence_db.execute("SELECT id FROM offer_fetch").fetchall() == [(unrelated,)]
    assert sentinel.read_text() == "Unrelated user-owned sentinel"
    assert evidence_db.execute("SELECT count(*) FROM source WHERE id='s'").fetchone() == (1,)


def test_unknown_permission_is_blocked_without_fabricated_termination(tmp_path):
    sentinel = tmp_path / "not-authorized-for-deletion.txt"
    sentinel.write_text("Preserve")
    unknown = policy(allowed=False)
    assert status(unknown, NOW) == "blocked"
    assert purge(tmp_path, [sentinel.name], unknown, NOW, execute=True) == ()
    assert sentinel.read_text() == "Preserve"
