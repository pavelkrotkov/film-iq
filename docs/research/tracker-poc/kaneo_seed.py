"""Seed fictional films in a dedicated Kaneo test project, never TMDB.

Reruns reuse existing fixture IDs and fill missing synthetic critic fields.
This does not store per-user preferences and is not safe for simultaneous
seeders; stop if duplicate IDs are found.
"""

import argparse
import http.cookiejar
import json
import time
import urllib.request
from pathlib import Path

from fixture_data import generate
from kaneo_smoke import call, ensure_field


def seed(base: str, project: str, cookie_file: Path, count: int):
    cookies = http.cookiejar.MozillaCookieJar(str(cookie_file))
    cookies.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    identity = ensure_field(opener, base, project, "POC Fixture ID", "text")
    year = ensure_field(opener, base, project, "POC Year", "number")
    genre = ensure_field(opener, base, project, "POC Genre", "text")
    critic = ensure_field(opener, base, project, "POC Critic Score", "number")
    summary = ensure_field(opener, base, project, "POC Critic Summary", "text")
    providers = ensure_field(
        opener,
        base,
        project,
        "POC Subscription Providers",
        "multiselect",
        ["Netflix", "Hulu", "Criterion Channel"],
    )
    values = call(opener, base, f"/custom-field/project/{project}/values")
    ids = [row["value"] for row in values if row["fieldId"] == identity]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate fixture IDs; refusing to seed")
    present = {row["value"]: row["taskId"] for row in values if row["fieldId"] == identity}
    populated = {(row["taskId"], row["fieldId"]) for row in values if row["value"]}
    states = {
        "Discovery": "to-do",
        "Evaluation": "in-progress",
        "Watchlist": "in-review",
        "Archived": "done",
    }
    started = time.monotonic()
    added = 0
    updated = 0
    for film in generate(count)["films"]:
        if film["fixture_id"] in present:
            task = present[film["fixture_id"]]
            for field, value in (
                (critic, str(film["critic_score"])),
                (summary, film["critic_summary"]),
            ):
                if (task, field) not in populated:
                    call(
                        opener,
                        base,
                        "/custom-field/value",
                        {"taskId": task, "fieldId": field, "value": value},
                        "PUT",
                    )
                    updated += 1
            continue
        fields = [
            {"fieldId": identity, "value": film["fixture_id"]},
            {"fieldId": year, "value": str(film["release_year"])},
            {"fieldId": genre, "value": film["genres"][0]},
            {"fieldId": providers, "value": json.dumps(film["streaming_providers"])},
            {"fieldId": critic, "value": str(film["critic_score"])},
            {"fieldId": summary, "value": film["critic_summary"]},
        ]
        call(
            opener,
            base,
            f"/task/{project}",
            {
                "title": film["title"],
                "description": film["synopsis"],
                "priority": "no-priority",
                "status": states[film["lifecycle_state"]],
                "customFields": fields,
            },
        )
        added += 1
    print(
        f"Created {added} fixtures and filled {updated} missing critic fields in {time.monotonic() - started:.2f}s"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--project", required=True)
    parser.add_argument("--cookie-file", required=True, type=Path)
    parser.add_argument("--count", type=int, default=30)
    args = parser.parse_args()
    seed(args.base.rstrip("/"), args.project, args.cookie_file, args.count)
