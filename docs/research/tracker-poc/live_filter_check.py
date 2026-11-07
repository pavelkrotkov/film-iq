"""Join live synthetic Kaneo records and both users' POC preferences."""

import argparse
import json
import subprocess
from pathlib import Path

from kaneo_smoke import call
from preferences_check import login, preference_request


def check(directory: Path):
    ids = json.loads((directory / "kaneo-ids.json").read_text())
    user_a = login(directory / "kaneo-test-user.json")
    user_b = login(directory / "kaneo-viewer.json")
    base = "http://localhost:15173"
    rows = call(user_a, base, f"/custom-field/project/{ids['project']}/values")
    fields = {}
    for row in rows:
        fields.setdefault(row["taskId"], {})[row["fieldName"]] = row["value"]
    films, page, pages, total = [], 1, 1, None
    while page <= pages:
        response = call(user_a, base, f"/task/tasks/{ids['project']}?limit=100&page={page}")
        pagination = response["pagination"]
        if total is not None and total != pagination["total"]:
            raise ValueError("board changed during test")
        pages, total = pagination["totalPages"], pagination["total"]
        board = response["data"]
        films.extend(task for column in board["columns"] for task in column["tasks"])
        films.extend(board["archivedTasks"] + board["plannedTasks"])
        page += 1
    if len(films) != total or len({film["id"] for film in films}) != total:
        raise ValueError("incomplete board traversal")
    for film in films:
        film["fields"] = fields.get(film["id"], {})
    data = {
        "films": films,
        "userA": preference_request(user_a, "/preferences")["preferences"],
        "userB": preference_request(user_b, "/preferences")["preferences"],
    }
    script = Path(__file__).parent / "ui/live_filter_check.mjs"
    subprocess.run(["node", str(script)], input=json.dumps(data), text=True, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    check(args.directory)
