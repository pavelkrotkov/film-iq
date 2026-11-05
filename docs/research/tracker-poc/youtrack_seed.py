"""Seed the synthetic YouTrack project with the common fictional dataset."""

import argparse
import json
import time
from typing import Any

from fixture_data import generate
from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import ISSUE_FIELDS, custom_value
from youtrack_setup import ensure_fields, ensure_lifecycle, project_id


def simple(name: str, value: Any) -> dict[str, Any]:
    return {"name": name, "$type": "SimpleIssueCustomField", "value": value}


def text_field(name: str, value: str) -> dict[str, Any]:
    return {"name": name, "$type": "TextIssueCustomField", "value": {"text": value}}


def seed(client: YouTrackClient, count: int) -> tuple[int, int, float]:
    project = project_id(client)
    ensure_fields(client, project)
    ensure_lifecycle(client, project)
    issues = client.pages(
        "issues",
        query={"fields": ISSUE_FIELDS, "query": "project: {FILMPOC} sort by: {issue id} asc"},
    )
    seen: set[int] = set()
    for issue in issues:
        key = custom_value(issue, "FilmIQ Fixture ID")
        if key is None:
            continue
        if type(key) is not int or key in seen:
            raise YouTrackError("Synthetic fixture IDs are invalid or duplicated")
        seen.add(key)
    start = time.monotonic()
    created = 0
    for index, film in enumerate(generate(count)["films"], 1):
        if index in seen:
            continue
        observation = {
            "source": "synthetic fixture, not TMDB",
            "subscription": film["streaming_providers"],
            "rent": film["rental_providers"],
            "checked_at": film["availability_checked_at"],
        }
        result = client.request(
            "issues",
            query={"fields": "id"},
            body={
                "project": {"id": project},
                "summary": film["title"],
                "description": film["synopsis"],
                "customFields": [
                    simple("FilmIQ Fixture ID", index),
                    simple("FilmIQ Release Year", film["release_year"]),
                    simple("FilmIQ Genre", film["genres"][0]),
                    simple("FilmIQ Critic Score", film["critic_score"]),
                    text_field("FilmIQ Critic Summary", film["critic_summary"]),
                    text_field(
                        "FilmIQ Provider Observation", json.dumps(observation, sort_keys=True)
                    ),
                    {
                        "name": "FilmIQ Lifecycle",
                        "$type": "StateIssueCustomField",
                        "value": {"name": film["lifecycle_state"]},
                    },
                ],
            },
        )
        if not isinstance(result, dict) or not isinstance(result.get("id"), str):
            raise YouTrackError("Fixture creation outcome uncertain; inspect before retrying")
        seen.add(index)
        created += 1
    return created, count - created, time.monotonic() - start


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=30)
    args = parser.parse_args()
    if args.count < 1:
        raise SystemExit("Count must be positive")
    created, existing, elapsed = seed(YouTrackClient(), args.count)
    print(f"Synthetic YouTrack seed: {created} created, {existing} existing, {elapsed:.3f}s")


if __name__ == "__main__":
    main()
