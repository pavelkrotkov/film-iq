"""Import canonical records from the ignored private input into local YouTrack.

This deliberately does not transfer Movary watched status, notes, ratings,
or watchlist state. Repeat runs leave existing issues untouched. TMDB API
responses are not imported; source-listed years are not release years.
Run only one importer at a time.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from youtrack_client import ROOT, YouTrackClient, YouTrackError
from youtrack_enrich import ISSUE_FIELDS, custom_value
from youtrack_setup import ensure_fields, ensure_lifecycle

SOURCE = ROOT / ".cache/tracker-poc/private/film-input.json"
PROJECT = "FILMREAL"


def validate(path: Path) -> list[dict[str, Any]]:
    source = json.loads(path.read_text(encoding="utf-8"))
    films = source.get("films") if isinstance(source, dict) else None
    if not isinstance(films, list) or not films:
        raise ValueError("Private input contains no films")
    seen: set[int] = set()
    for film in films:
        if not isinstance(film, dict):
            raise ValueError("Invalid private film record")
        identity, title = film.get("tmdb_id"), film.get("title")
        if (
            type(identity) is not int
            or identity <= 0
            or not isinstance(title, str)
            or not title.strip()
        ):
            raise ValueError("A film has an invalid identity or title")
        if identity in seen:
            raise ValueError("Private input has a duplicate TMDB identifier")
        seen.add(identity)
        if film.get("release_year") is not None:
            raise ValueError("Source-listed years must not be treated as canonical release years")
        year = film.get("source_year")
        if year is not None and (type(year) is not int or not 1800 <= year <= 2100):
            raise ValueError("Invalid source-listed year")
        director = film.get("director")
        if director is not None and not isinstance(director, str):
            raise ValueError("Invalid source-listed director")
        evidence = film.get("accepted_discovery_evidence")
        if evidence is not None and not isinstance(evidence, dict):
            raise ValueError("Invalid source evidence")
    return films


def ensure_project(client: YouTrackClient) -> str:
    projects = client.pages("admin/projects", query={"fields": "id,name,shortName"})
    matches = [item for item in projects if item.get("shortName") == PROJECT]
    if len(matches) > 1:
        raise YouTrackError("Film project is ambiguous")
    if matches:
        return str(matches[0]["id"])
    me = client.request("users/me", query={"fields": "id"})
    project = client.request(
        "admin/projects",
        query={"fields": "id,name,shortName"},
        body={
            "name": "FilmIQ Local Film POC",
            "shortName": PROJECT,
            "leader": {"id": me["id"]},
            "description": "Private local film comparison experiment.",
        },
    )
    if not isinstance(project, dict) or not isinstance(project.get("id"), str):
        raise YouTrackError("Project creation response lacked an ID; check before retrying")
    return str(project["id"])


def field(name: str, value: Any) -> dict[str, Any]:
    return {"name": name, "$type": "SimpleIssueCustomField", "value": value}


def issue_body(film: dict[str, Any], project: str) -> dict[str, Any]:
    custom: list[dict[str, Any]] = [
        field("FilmIQ TMDB ID", film["tmdb_id"]),
        {
            "name": "FilmIQ Lifecycle",
            "$type": "StateIssueCustomField",
            "value": {"name": "Discovery"},
        },
    ]
    if film.get("source_year") is not None:
        custom.append(field("FilmIQ Source Year", film["source_year"]))
    if film.get("director"):
        custom.append(field("FilmIQ Director", film["director"]))
    evidence = film.get("accepted_discovery_evidence") or {}
    if evidence.get("links"):
        custom.append(
            {
                "name": "FilmIQ Source Evidence",
                "$type": "TextIssueCustomField",
                "value": {"text": json.dumps(evidence, ensure_ascii=False, sort_keys=True)},
            }
        )
    return {"project": {"id": project}, "summary": film["title"], "customFields": custom}


def run(client: YouTrackClient, films: list[dict[str, Any]]) -> tuple[int, int]:
    project = ensure_project(client)
    ensure_fields(client, project)
    ensure_lifecycle(client, project)
    issues = client.pages(
        "issues",
        query={"fields": ISSUE_FIELDS, "query": "project: {FILMREAL} sort by: {issue id} asc"},
    )
    indexed: set[int] = set()
    for issue in issues:
        identity = custom_value(issue, "FilmIQ TMDB ID")
        if identity is None:
            continue
        if type(identity) is not int or identity in indexed:
            raise YouTrackError(
                "Existing film IDs are invalid or duplicated; manual review required"
            )
        indexed.add(identity)
    created = 0
    for film in films:
        if film["tmdb_id"] in indexed:
            continue
        result = client.request("issues", query={"fields": "id"}, body=issue_body(film, project))
        if not isinstance(result, dict) or not isinstance(result.get("id"), str):
            raise YouTrackError("Creation outcome uncertain; inspect the project before retrying")
        indexed.add(film["tmdb_id"])
        created += 1
    return created, len(films) - created


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="write canonical issues to local YouTrack"
    )
    args = parser.parse_args()
    films = validate(SOURCE)
    if not args.apply:
        print(f"Validated {len(films)} private films; no changes made")
        return
    created, existing = run(YouTrackClient(), films)
    print(f"YouTrack canonical import: {created} created, {existing} already present")


if __name__ == "__main__":
    main()
