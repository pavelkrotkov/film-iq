"""Seed two synthetic users' preferences for existing synthetic Kaneo films."""

import argparse
import json
from pathlib import Path

from fixture_data import generate
from kaneo_smoke import call
from preferences_check import login, preference_request


def seed(directory: Path, count: int):
    ids = json.loads((directory / "kaneo-ids.json").read_text())
    users = {
        "user-a": login(directory / "kaneo-test-user.json"),
        "user-b": login(directory / "kaneo-viewer.json"),
    }
    rows = call(
        users["user-a"], "http://localhost:15173", f"/custom-field/project/{ids['project']}/values"
    )
    identities = [row for row in rows if row["fieldName"] == "POC Fixture ID"]
    tasks = {row["value"]: row["taskId"] for row in identities}
    if len(tasks) != len(identities):
        raise ValueError("duplicate synthetic fixture IDs")
    dataset = generate(count)
    if any(film["fixture_id"] not in tasks for film in dataset["films"]):
        raise ValueError("run the film seeder for this count first")
    existing = {
        user: preference_request(opener, "/preferences")["preferences"]
        for user, opener in users.items()
    }
    changed = 0
    for row in dataset["preferences"]:
        task = tasks.get(row["fixture_id"])
        if not task:
            raise ValueError("run the film seeder for this count first")
        user = row["user_id"]
        proposal = {
            key: row[key] for key in ("interest_score", "watchlist", "watched_at", "personal_notes")
        }
        if existing[user].get(task) == proposal:
            continue
        preview = preference_request(
            users[user], "/preview/" + task, "POST", {"preference": proposal}
        )
        preference_request(
            users[user],
            "/preferences/" + task,
            "PUT",
            {"preference": proposal, "token": preview["token"]},
        )
        changed += 1
    print(f"Seeded {changed} synthetic preference records after preview")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--count", type=int, default=30)
    args = parser.parse_args()
    seed(args.directory, args.count)
