"""Provider permission/expiry summaries do not expose rights evidence or payloads."""

import json
from datetime import UTC, datetime, timedelta

from film_iq.availability.policies import record_policy
from film_iq.cli import main
from film_iq.recovery import backup
from film_iq.retention import CachePolicy
from film_iq.storage import connect, migrate


def test_expired_policy_needs_attention_without_modifying_data(tmp_path, capsys):
    path = tmp_path / "evidence.db"
    now = datetime(2026, 10, 31, tzinfo=UTC)
    with connect(tmp_path / "source.db") as db:
        migrate(db)
        policy = CachePolicy(
            "synthetic",
            True,
            "private rights evidence",
            "private attribution",
            now - timedelta(seconds=1),
        )
        record_policy(db, policy, now)
        backup(db, path)
    before = path.read_bytes()
    assert (
        main(["status", "--database", str(path), "--now", now.isoformat(), "--format", "json"]) == 1
    )
    output = capsys.readouterr().out
    assert json.loads(output)["provider_policies"]["purge_due"] == 1
    assert "private" not in output and path.read_bytes() == before
