"""Import canonical records from the ignored private input into local YouTrack.

This deliberately does not transfer Movary watched status, notes, ratings,
or watchlist state. Repeat runs only fill missing sanitized provenance fields;
they do not replace existing values. TMDB API responses are not imported;
source-listed years are not release years. Run only one importer at a time.
"""

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

from youtrack_client import ROOT, YouTrackClient, YouTrackError
from youtrack_enrich import ISSUE_FIELDS, custom_value
from youtrack_setup import ensure_fields, ensure_lifecycle

SOURCE = ROOT / ".cache/tracker-poc/private/film-input.json"
PROJECT = "FILMREAL"
PROVENANCE_FIELD = "FilmIQ Field Provenance"
LINK_FIELDS = {
    "url",
    "source_id",
    "kind",
    "author",
    "edition",
    "published_at",
    "rank",
    "tie",
    "locator",
    "lineage_kind",
    "lineage",
    "entry_id",
    "revision_id",
}


def validate_evidence(value: Any, identity: int) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"tmdb_id", "status", "links"}
        or type(value.get("tmdb_id")) is not int
        or value["tmdb_id"] != identity
        or value.get("status") not in ("available", "unknown")
        or not isinstance(value.get("links"), list)
        or bool(value["links"]) != (value["status"] == "available")
    ):
        raise ValueError("Source evidence is invalid or belongs to a different film")
    for link in value["links"]:
        if not isinstance(link, dict) or set(link) != LINK_FIELDS:
            raise ValueError("Source evidence link is malformed")
        if not all(
            isinstance(link.get(k), str) and link[k].strip()
            for k in ("url", "entry_id", "revision_id")
        ):
            raise ValueError("Source evidence link lacks an ID or URL")
        try:
            url = urlsplit(link["url"])
            if (
                url.scheme not in {"http", "https"}
                or not url.hostname
                or url.username is not None
                or url.password is not None
            ):
                raise ValueError("invalid URL")
        except ValueError:
            raise ValueError("Source evidence link URL is invalid") from None
        for key, item in link.items():
            if key == "rank":
                if item is not None and (type(item) is not int or item < 1):
                    raise ValueError("Source evidence rank is invalid")
            elif key == "tie":
                if item is not None and not isinstance(item, (str, bool)):
                    raise ValueError("Source evidence tie is invalid")
            elif item is not None and not isinstance(item, str):
                raise ValueError("Source evidence link metadata is invalid")


def shared_provenance(film: dict[str, Any], issue: dict[str, Any] | None = None) -> dict[str, str]:
    """Keep only generic, non-personal provenance in shared issue fields."""
    source = film.get("field_provenance")
    if not isinstance(source, dict):
        raise ValueError("Field provenance is missing")
    identity = source.get("tmdb_id")
    title = source.get("title")
    if identity == "reviewed accepted identity match":
        identity_origin = "reviewed accepted identity match"
    elif identity == "Movary API or native export; not independently reverified here":
        identity_origin = "supplied identifier; independently unverified"
    else:
        raise ValueError("Unsupported identity provenance")
    if title == "accepted source-list observation":
        title_origin = "accepted source-list observation"
    elif title == "Movary API or native export; upstream catalog origin is unknown":
        title_origin = "private catalogue input; upstream origin and retention unverified"
    else:
        raise ValueError("Unsupported title provenance")
    result = {
        "scope": "At creation or backfill; later edits require revalidation",
        "tmdb_id": identity_origin,
        "title": title_origin,
        "source_year": "source-listed assertion, not a canonical release year"
        if film.get("source_year") is not None
        else "unknown",
        "director": "source-listed assertion" if film.get("director") else "unknown",
        "release_year": "unknown",
    }
    if issue is not None:
        if issue.get("summary") != film["title"]:
            result["title"] = "current value differs from input; origin unknown"
        if custom_value(issue, "FilmIQ Source Year") != film.get("source_year"):
            result["source_year"] = "current value differs from input; origin unknown"
        if custom_value(issue, "FilmIQ Director") != (film.get("director") or None):
            result["director"] = "current value differs from input; origin unknown"
    return result


def validate(path: Path) -> list[dict[str, Any]]:
    source = json.loads(path.read_text(encoding="utf-8"))
    films = source.get("films") if isinstance(source, dict) else None
    if not isinstance(source, dict) or source.get("version") != "tracker-poc-private-film-input-v1":
        raise ValueError("Unsupported private input version")
    if not isinstance(films, list):
        raise ValueError("Private input contains no film list")
    validate_films(films)
    return films


def validate_films(films: Any) -> None:
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
        validate_evidence(film.get("accepted_discovery_evidence"), identity)
        shared_provenance(film)


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
    custom.append(
        {
            "name": PROVENANCE_FIELD,
            "$type": "TextIssueCustomField",
            "value": {
                "text": json.dumps(shared_provenance(film), ensure_ascii=False, sort_keys=True)
            },
        }
    )
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


def run(client: YouTrackClient, films: list[dict[str, Any]]) -> tuple[int, int, int]:
    validate_films(films)
    project = ensure_project(client)
    ensure_fields(client, project)
    ensure_lifecycle(client, project)
    issues = client.pages(
        "issues",
        query={"fields": ISSUE_FIELDS, "query": "project: {FILMREAL} sort by: {issue id} asc"},
    )
    indexed: dict[int, dict[str, Any]] = {}
    for issue in issues:
        identity = custom_value(issue, "FilmIQ TMDB ID")
        if identity is None:
            continue
        if type(identity) is not int or identity in indexed:
            raise YouTrackError(
                "Existing film IDs are invalid or duplicated; manual review required"
            )
        indexed[identity] = issue
    created = backfilled = 0
    for film in films:
        if film["tmdb_id"] in indexed:
            original = indexed[film["tmdb_id"]]
            if custom_value(original, PROVENANCE_FIELD) is not None:
                continue
            issue_id = original.get("id")
            if not isinstance(issue_id, str):
                raise YouTrackError("Existing issue has no ID")
            path = "issues/" + quote(issue_id, safe="")
            current = client.request(path, query={"fields": ISSUE_FIELDS})
            if custom_value(current, "FilmIQ TMDB ID") != film["tmdb_id"]:
                raise YouTrackError("Existing film identity changed during import")
            if custom_value(current, PROVENANCE_FIELD) is None:
                client.request(
                    path,
                    body={
                        "customFields": [
                            {
                                "name": PROVENANCE_FIELD,
                                "$type": "TextIssueCustomField",
                                "value": {
                                    "text": json.dumps(
                                        shared_provenance(film, current),
                                        ensure_ascii=False,
                                        sort_keys=True,
                                    )
                                },
                            }
                        ]
                    },
                )
                backfilled += 1
            continue
        result = client.request("issues", query={"fields": "id"}, body=issue_body(film, project))
        if not isinstance(result, dict) or not isinstance(result.get("id"), str):
            raise YouTrackError("Creation outcome uncertain; inspect the project before retrying")
        indexed[film["tmdb_id"]] = result
        created += 1
    return created, len(films) - created, backfilled


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
    created, existing, backfilled = run(YouTrackClient(), films)
    print(
        f"YouTrack canonical import: {created} created, {existing} already present, {backfilled} provenance fields filled"
    )


if __name__ == "__main__":
    main()
