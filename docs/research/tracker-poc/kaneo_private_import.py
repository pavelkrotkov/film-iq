"""Create missing canonical records in a dedicated local Kaneo POC project.

Existing records are never updated. The identity index is checked on every run;
creation sends the identity and all initial custom fields in one task request.
Run one importer at a time. Watched history remains in the separate private
Movary snapshot/manifest; no ratings, notes or watchlist state are copied.
"""

import argparse
import http.cookiejar
import json
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from kaneo_smoke import call, ensure_field

PUBLIC_IDENTITY_PROVENANCE = "Source-provided film identity; not independently verified."
PUBLIC_FIELD_PROVENANCE = json.dumps(
    {
        "identity": PUBLIC_IDENTITY_PROVENANCE,
        "details": "Exact source provenance is retained privately.",
    },
    ensure_ascii=False,
)

FIELD_TYPES = {
    "POC TMDB ID": "text",
    "POC Identity Provenance": "text",
    "POC Field Provenance": "text",
    "POC Source Year": "number",
    "POC Source Director": "text",
    "POC Evidence": "text",
}


def validate(manifest: dict) -> None:
    if manifest.get("version") != "tracker-poc-private-film-input-v1":
        raise ValueError("unsupported private input version")
    if not isinstance(manifest.get("films"), list):
        raise ValueError("missing film list")
    ids = set()
    for film in manifest["films"]:
        ident = film.get("tmdb_id")
        if type(ident) is not int or ident <= 0 or ident in ids:
            raise ValueError("film identifiers must be unique positive integers")
        ids.add(ident)
        if not isinstance(film.get("title"), str) or not film["title"].strip():
            raise ValueError("film title is missing")
        if not isinstance(film.get("field_provenance"), dict):
            raise ValueError("film provenance is missing")
        year = film.get("source_year")
        if year is not None and (type(year) is not int or not 1800 <= year <= 2200):
            raise ValueError("source year is invalid")
        evidence = film.get("accepted_discovery_evidence")
        if not isinstance(evidence, dict) or evidence.get("tmdb_id") != ident:
            raise ValueError("source evidence identity is missing or inconsistent")
        if evidence.get("status") not in ("available", "unknown") or not isinstance(
            evidence.get("links"), list
        ):
            raise ValueError("invalid source evidence")


def import_films(opener, base: str, project: str, manifest: dict) -> dict:
    """Create missing records, returning identifiers without private film content."""
    validate(manifest)
    fields = {
        name: ensure_field(opener, base, project, name, kind) for name, kind in FIELD_TYPES.items()
    }
    values = call(opener, base, f"/custom-field/project/{project}/values")
    present = {}
    for row in values:
        if row["fieldId"] != fields["POC TMDB ID"] or not row["value"]:
            continue
        if row["value"] in present:
            raise ValueError("project contains duplicate external identifiers")
        present[row["value"]] = row["taskId"]

    created = 0
    mapping = {}
    for film in manifest["films"]:
        identity = str(film["tmdb_id"])
        if identity not in present:
            attributes = {
                "POC TMDB ID": identity,
                "POC Identity Provenance": PUBLIC_IDENTITY_PROVENANCE,
                "POC Field Provenance": PUBLIC_FIELD_PROVENANCE,
                "POC Source Year": str(film["source_year"]) if film.get("source_year") else None,
                "POC Source Director": film.get("director"),
                "POC Evidence": json.dumps(film["accepted_discovery_evidence"], ensure_ascii=False),
            }
            custom_fields = [
                {"fieldId": fields[name], "value": value}
                for name, value in attributes.items()
                if isinstance(value, str) and value
            ]
            result = call(
                opener,
                base,
                f"/task/{project}",
                {
                    "title": film["title"],
                    "description": "",
                    "priority": "no-priority",
                    "status": "to-do",
                    "customFields": custom_fields,
                },
            )
            present[identity] = result["id"]
            created += 1
        mapping[identity] = present[identity]
    return {"project": project, "created": created, "mapping": mapping}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--project", required=True)
    parser.add_argument("--cookie-file", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    parsed = urlsplit(args.base)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("This experiment only supports a local loopback instance")
    cookies = http.cookiejar.MozillaCookieJar(str(args.cookie_file))
    cookies.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    result = import_films(
        opener, args.base.rstrip("/"), args.project, json.loads(args.input.read_text())
    )
    print(f"Created {result['created']} records; retained {len(result['mapping'])} identities")


if __name__ == "__main__":
    main()
