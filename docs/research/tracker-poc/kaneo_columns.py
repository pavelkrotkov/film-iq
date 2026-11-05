"""Name the default board columns for the isolated Kaneo film POC."""

import argparse
from pathlib import Path

from kaneo_smoke import call
from preferences_check import login

NAMES = {
    "to-do": ("To Do", "Discovery"),
    "in-progress": ("In Progress", "Evaluation"),
    "in-review": ("In Review", "Watchlist"),
    "done": ("Done", "Completed"),
}


def configure(directory: Path, project: str) -> None:
    opener = login(directory / "kaneo-test-user.json")
    base = "http://localhost:15173"
    columns = call(opener, base, f"/column/{project}")
    by_slug = {column["slug"]: column for column in columns}
    if any(
        slug not in by_slug or by_slug[slug]["name"] not in names for slug, names in NAMES.items()
    ):
        raise ValueError("Unexpected board configuration; no column changes were attempted")
    for slug, (_, name) in NAMES.items():
        if by_slug[slug]["name"] != name:
            call(opener, base, f"/column/{by_slug[slug]['id']}", {"name": name}, "PUT")
    observed = {
        column["slug"]: column["name"] for column in call(opener, base, f"/column/{project}")
    }
    if any(observed.get(slug) != names[1] for slug, names in NAMES.items()):
        raise RuntimeError("Board names did not all persist; inspect before retrying")
    print("Configured synthetic film board columns; original status slugs are unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    configure(args.directory, args.project)
