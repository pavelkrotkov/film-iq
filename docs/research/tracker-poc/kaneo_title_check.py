"""Verify title editing and authorization using one restored synthetic record."""

import argparse
import json
import urllib.error
from pathlib import Path

from kaneo_smoke import call
from preferences_check import login


def check(directory: Path) -> None:
    base = "http://localhost:15173"
    project = json.loads((directory / "kaneo-ids.json").read_text())["project"]
    owner = login(directory / "kaneo-test-user.json")
    viewer = login(directory / "kaneo-viewer.json")
    rows = call(owner, base, f"/custom-field/project/{project}/values")
    matches = [
        row["taskId"]
        for row in rows
        if row["fieldName"] == "POC Fixture ID" and row["value"] == "fixture-0003"
    ]
    if len(matches) != 1:
        raise ValueError("synthetic fixture 0003 must exist exactly once")
    task = matches[0]
    original = call(owner, base, f"/task/{task}")["title"]
    replacement = "Synthetic Rename Search Check"
    try:
        call(owner, base, f"/task/title/{task}", {"title": replacement}, "PUT")
        assert call(owner, base, f"/task/{task}")["title"] == replacement
        page = 1
        found = []
        while True:
            board = call(owner, base, f"/task/tasks/{project}?limit=100&page={page}")
            films = [film for column in board["data"]["columns"] for film in column["tasks"]]
            films += board["data"]["archivedTasks"] + board["data"]["plannedTasks"]
            found.extend(
                film
                for film in films
                if film["id"] == task and "rename search" in film["title"].lower()
            )
            if page >= board["pagination"]["totalPages"]:
                break
            page += 1
        assert len(found) == 1
        try:
            call(viewer, base, f"/task/title/{task}", {"title": "Unauthorized"}, "PUT")
        except urllib.error.HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError("viewer unexpectedly renamed the synthetic film")
        assert call(owner, base, f"/task/{task}")["title"] == replacement
    finally:
        call(owner, base, f"/task/title/{task}", {"title": original}, "PUT")
    assert call(owner, base, f"/task/{task}")["title"] == original
    print("Synthetic film rename, board search, viewer rejection and restoration passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    check(parser.parse_args().directory)
