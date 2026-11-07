"""Exercise synthetic film lifecycle while preserving the original test state."""

import argparse
import json
from pathlib import Path

from kaneo_smoke import call
from preferences_check import login, preference_request


def check(directory: Path) -> None:
    ids = json.loads((directory / "kaneo-ids.json").read_text())
    first = login(directory / "kaneo-test-user.json")
    second = login(directory / "kaneo-viewer.json")
    base = "http://localhost:15173"
    rows = call(first, base, f"/custom-field/project/{ids['project']}/values")
    matches = [
        row["taskId"]
        for row in rows
        if row["fieldName"] == "POC Fixture ID" and row["value"] == "fixture-0002"
    ]
    if len(matches) != 1:
        raise ValueError("fixture 0002 must exist exactly once")
    task = matches[0]
    original = call(first, base, f"/task/{task}")
    original_fields = call(first, base, f"/custom-field/task/{task}")
    personal = [
        preference_request(user, "/preferences")["preferences"].get(task)
        for user in (first, second)
    ]
    try:
        # These are the actual Kaneo statuses mapped in the POC UI; archive is
        # Kaneo's native archived status, distinct from the board's done column.
        for state in ("to-do", "in-progress", "in-review", "done", "archived"):
            call(first, base, f"/task/status/{task}", {"status": state}, "PUT")
            observed = call(first, base, f"/task/{task}")
            assert observed["status"] == state
            assert observed["title"] == original["title"]
            assert observed["description"] == original["description"]
            assert call(first, base, f"/custom-field/task/{task}") == original_fields
            assert [
                preference_request(user, "/preferences")["preferences"].get(task)
                for user in (first, second)
            ] == personal
    finally:
        call(first, base, f"/task/status/{task}", {"status": original["status"]}, "PUT")
    assert call(first, base, f"/task/{task}")["status"] == original["status"]
    print("Synthetic film traversed five Kaneo statuses; metadata and both preferences persisted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    check(parser.parse_args().directory)
