"""The real report reader must see an upgraded schema before its first query."""

import json
from pathlib import Path
from unittest.mock import Mock

from discovery_fixtures import cohort, fresh_status, snapshot
from operations_support import configuration

from film_iq import operations_run
from film_iq.discovery_command import discovery_command
from film_iq.storage import connect


def test_schema_eight_is_upgraded_before_discovery(tmp_path, monkeypatch):
    _, paths = configuration(tmp_path, monkeypatch)
    with connect(paths["database"]) as db:
        db.executescript("""
            DROP TABLE recognition_snapshot; DROP TABLE entry_recognition;
        DROP TABLE offer_event; DROP TABLE offer_current; DROP TABLE offer_fetch; DROP TABLE offer_purge; DROP TABLE offer_policy;
        DROP TABLE entry_ballot; DROP TABLE source_ballot;
            DROP TABLE acquisition_cursor; DROP TABLE acquisition_attempt;
            DROP TABLE acquisition_permission;
            DROP INDEX list_entry_ballot_key;
            PRAGMA user_version=8;
        """)
    paths["cohort"].write_text(json.dumps(cohort()))
    paths["snapshot"].write_text(json.dumps(snapshot()))
    status = Path(str(paths["snapshot"]) + ".status")
    status.write_text(json.dumps(fresh_status()))
    monkeypatch.setattr(operations_run, "discovery_command", discovery_command)
    result = operations_run.run_once(Mock(), **paths)
    assert result["stale"] is False
    with connect(paths["database"]) as db:
        assert db.execute("PRAGMA user_version").fetchone() == (11,)
        assert db.execute("SELECT count(*) FROM entry_ballot").fetchone() == (0,)
