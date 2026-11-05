"""Exercise fixture enrichment and failure preservation against local Kaneo."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from enrichment import FixtureSource, enrich
from kaneo_enrich import KaneoBackend
from kaneo_smoke import call, ensure_field


class PartialSource(FixtureSource):
    def availability(self, source_id: int) -> dict:
        return {
            "id": source_id,
            "results": {"US": {"link": "https://example.invalid", "flatrate": [{}]}},
        }


class FailedSource(FixtureSource):
    def availability(self, source_id: int) -> None:
        return None


class RaisingSource(FixtureSource):
    def availability(self, source_id: int) -> None:
        raise RuntimeError("simulated provider failure")


def check(base: str, directory: Path):
    ids = json.loads((directory / "kaneo-ids.json").read_text())
    backend = KaneoBackend(base, ids["project"], directory / "kaneo-cookies.txt")
    now = datetime(2026, 11, 5, tzinfo=UTC)
    record = enrich(FixtureSource(), backend, 42, now)
    call(
        backend.opener,
        base,
        f"/task/description/{record}",
        {"description": "User-maintained synthetic synopsis."},
        "PUT",
    )
    backend._set(record, backend.fields["genre"], "User genre")
    notes = ensure_field(backend.opener, base, ids["project"], "POC User Notes", "text")
    backend._set(record, notes, "Synthetic user note")
    assert enrich(FixtureSource(), backend, 42, now) == record
    fields = call(backend.opener, base, f"/custom-field/task/{record}")
    values = {row["fieldId"]: row["value"] for row in fields}
    assert values[backend.fields["genre"]] == "User genre"
    assert values[notes] == "Synthetic user note"
    available = values[backend.fields["availability"]]
    decoded = json.loads(available)
    assert decoded["subscription"] == ["Fixture Stream"] and decoded["rent"] == ["Fixture Rental"]
    assert enrich(PartialSource(), backend, 42, now) == record
    assert enrich(FailedSource(), backend, 42, now) == record
    try:
        enrich(RaisingSource(), backend, 42, now)
    except RuntimeError as error:
        assert str(error) == "simulated provider failure"
    else:
        raise AssertionError("provider failure was not propagated")
    refreshed = call(backend.opener, base, f"/custom-field/task/{record}")
    assert (
        next(row["value"] for row in refreshed if row["fieldId"] == backend.fields["availability"])
        == available
    )
    assert (
        call(backend.opener, base, f"/task/{record}")["description"]
        == "User-maintained synthetic synopsis."
    )
    all_values = call(backend.opener, base, f"/custom-field/project/{ids['project']}/values")
    assert (
        len(
            [
                row
                for row in all_values
                if row["fieldId"] == backend.fields["identity"] and row["value"] == "42"
            ]
        )
        == 1
    )
    print("Fixture import, repeat, user fields and failed/partial availability preservation passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    check(args.base.rstrip("/"), args.directory)
