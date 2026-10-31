"""Named synthetic copies expire together; no live artifact discovery or cleanup."""

import json
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
    inventory = json.loads((tmp_path / "retention-manifest.json").read_text())
    databases = ("online.sqlite", "isolated/online.sqlite", "restored.sqlite")
    assert [copied_deadline(tmp_path / name, identifier) for name in databases] == [
        EXPIRY.isoformat()
    ] * 3
    assert copied_deadline(tmp_path / "online.sqlite", unrelated) > deadline
    sentinel = tmp_path / "user-owned.txt"
    sentinel.write_text("Unrelated user-owned sentinel")
    decision = replace(policy(allowed=True), terminated=terminated)
    now = NOW if terminated else EXPIRY
    if terminated:
        record_policy(evidence_db, decision, now)
    assert (
        status(decision, now),
        purge(tmp_path, inventory["names"], decision, now),
        purge_source(evidence_db, "fixture", now),
    ) == ("purge_due", tuple(names), (identifier,))
    assert (
        [(tmp_path / name).exists() for name in names],
        copied_deadline(tmp_path / "online.sqlite", identifier),
        evidence_db.execute("SELECT id FROM offer_fetch WHERE source='fixture'").fetchall(),
    ) == ([True] * len(names), deadline, [(identifier,)])
    purge(tmp_path, inventory["names"], decision, now, execute=True)
    purge_source(evidence_db, "fixture", now, execute=True)
    assert (
        [(tmp_path / name).exists() for name in names],
        evidence_db.execute("SELECT id FROM offer_fetch").fetchall(),
        sentinel.read_text(),
        evidence_db.execute("SELECT count(*) FROM source WHERE id='s'").fetchone(),
    ) == ([False] * len(names), [(unrelated,)], "Unrelated user-owned sentinel", (1,))
