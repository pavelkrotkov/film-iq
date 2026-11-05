"""Create the small set of typed fields used by the local YouTrack POC."""

from typing import Any
from urllib.parse import quote

from youtrack_client import YouTrackClient, YouTrackError

PROJECT = "FILMPOC"
FIELDS = {
    "FilmIQ Fixture ID": "integer",
    "FilmIQ TMDB ID": "integer",
    "FilmIQ Release Year": "integer",
    "FilmIQ Source Year": "integer",
    "FilmIQ Director": "string",
    "FilmIQ Genre": "string",
    "FilmIQ Critic Score": "integer",
    "FilmIQ Critic Summary": "text",
    "FilmIQ Source Evidence": "text",
    "FilmIQ Field Provenance": "text",
    "FilmIQ Provider Observation": "text",
    "FilmIQ POC Schedule Marker": "string",
}


def project_id(client: YouTrackClient, short_name: str = PROJECT) -> str:
    projects = client.pages("admin/projects", query={"fields": "id,shortName,name"})
    matches = [project for project in projects if project.get("shortName") == short_name]
    if len(matches) != 1:
        raise YouTrackError(f"The {short_name} project was not found uniquely")
    return str(matches[0]["id"])


def ensure_fields(client: YouTrackClient, project: str) -> None:
    base_path = "admin/customFieldSettings/customFields"
    fields = client.pages(base_path, query={"fields": "id,name,fieldType(id)"})
    project_path = f"admin/projects/{quote(project, safe='')}/customFields"
    attached = client.pages(project_path, query={"fields": "id,field(id,name,fieldType(id))"})
    attached_ids = {entry["field"]["id"] for entry in attached if entry.get("field")}
    for name, field_type in FIELDS.items():
        matches = [field for field in fields if field.get("name") == name]
        if len(matches) > 1:
            raise YouTrackError(f"Field name {name!r} is ambiguous")
        if matches:
            field: dict[str, Any] = matches[0]
            if field.get("fieldType", {}).get("id") != field_type:
                raise YouTrackError(f"Field {name!r} has an unexpected type")
        else:
            field = client.request(
                base_path,
                query={"fields": "id,name,fieldType(id)"},
                body={
                    "name": name,
                    "fieldType": {"id": field_type},
                    "isAutoAttached": False,
                    "isPublic": True,
                },
            )
        if field["id"] not in attached_ids:
            client.request(
                project_path,
                query={"fields": "id,field(id,name)"},
                body={
                    "field": {"id": field["id"]},
                    "$type": "TextProjectCustomField"
                    if field_type == "text"
                    else "SimpleProjectCustomField",
                    "canBeEmpty": True,
                },
            )


def ensure_lifecycle(client: YouTrackClient, project: str) -> None:
    """Use a dedicated state bundle so existing project states stay untouched."""
    base_path = "admin/customFieldSettings/customFields"
    fields = client.pages(base_path, query={"fields": "id,name,fieldType(id)"})
    matches = [entry for entry in fields if entry.get("name") == "FilmIQ Lifecycle"]
    if len(matches) > 1:
        raise YouTrackError("Lifecycle field name is ambiguous")
    field = (
        matches[0]
        if matches
        else client.request(
            base_path,
            query={"fields": "id,name,fieldType(id)"},
            body={
                "name": "FilmIQ Lifecycle",
                "fieldType": {"id": "state[1]"},
                "isAutoAttached": False,
            },
        )
    )
    if field.get("fieldType", {}).get("id") != "state[1]":
        raise YouTrackError("Lifecycle field has an unexpected type")
    bundles_path = "admin/customFieldSettings/bundles/state"
    bundles = client.pages(bundles_path, query={"fields": "id,name,values(id,name,isResolved)"})
    candidates = [item for item in bundles if item.get("name") == "FilmIQ POC Lifecycle"]
    if len(candidates) > 1:
        raise YouTrackError("Lifecycle bundle name is ambiguous")
    states = ["Discovery", "Evaluation", "Watchlist", "Archived"]
    bundle = (
        candidates[0]
        if candidates
        else client.request(
            bundles_path,
            query={"fields": "id,name,values(id,name,isResolved)"},
            body={
                "name": "FilmIQ POC Lifecycle",
                "values": [{"name": name, "isResolved": name == "Archived"} for name in states],
            },
        )
    )
    if {item["name"] for item in bundle.get("values", [])} != set(states):
        raise YouTrackError("Lifecycle bundle has unexpected values")
    project_path = f"admin/projects/{quote(project, safe='')}/customFields"
    attached = client.pages(project_path, query={"fields": "id,field(id,name),bundle(id)"})
    existing = [entry for entry in attached if entry.get("field", {}).get("id") == field["id"]]
    if len(existing) > 1:
        raise YouTrackError("Lifecycle field is attached more than once")
    if existing:
        if existing[0].get("bundle", {}).get("id") != bundle["id"]:
            raise YouTrackError("Lifecycle field uses an unexpected bundle")
        return
    client.request(
        project_path,
        query={"fields": "id,field(name),bundle(id)"},
        body={
            "field": {"id": field["id"], "$type": "CustomField"},
            "$type": "StateProjectCustomField",
            "bundle": {"id": bundle["id"], "$type": "StateBundle"},
            "canBeEmpty": True,
        },
    )


def main() -> None:
    client = YouTrackClient()
    project = project_id(client)
    ensure_fields(client, project)
    ensure_lifecycle(client, project)
    print("FilmIQ POC project and typed fields are ready")


if __name__ == "__main__":
    main()
