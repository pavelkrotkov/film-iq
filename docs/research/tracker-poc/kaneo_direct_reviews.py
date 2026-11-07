"""Preview or attach validated direct-review links to existing Kaneo POC records.

Never overwrites an existing review field value, including an explicit clear.
Run one importer at a time and do not edit the target field concurrently:
Kaneo does not expose compare-and-swap.
"""

import argparse
import http.cookiejar
import json
import os
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from direct_review_links import validate_review_manifests
from kaneo_smoke import call, ensure_field

FIELD = "POC Direct Review Links"
IDENTITY_FIELD = "POC TMDB ID"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward an integration credential to a redirect target."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api_key_opener(key: str | None):
    """Build an opt-in, server-side bearer client without browser sessions."""
    if not key or any(not 33 <= ord(char) <= 126 for char in key):
        raise ValueError("KANEO_API_KEY must be a nonempty ASCII key without whitespace")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    opener.addheaders = [("Authorization", f"Bearer {key}")]
    return opener


def import_reviews(
    opener,
    base: str,
    project: str,
    manifest: dict | list[dict],
    source: dict,
    *,
    apply: bool = False,
) -> dict:
    manifests = manifest if isinstance(manifest, list) else [manifest]
    rows, holdbacks = validate_review_manifests(manifests, source)
    definitions = call(opener, base, f"/custom-field/project/{project}")
    identity = [field for field in definitions if field["name"] == IDENTITY_FIELD]
    reviews = [field for field in definitions if field["name"] == FIELD]
    if (
        len(identity) != 1
        or identity[0]["type"] != "text"
        or len(reviews) > 1
        or (reviews and reviews[0]["type"] != "text")
    ):
        raise ValueError("ambiguous or invalid review/identity field")
    values = call(opener, base, f"/custom-field/project/{project}/values")
    identities = {}
    review_values = {}
    for value in values:
        if value["fieldId"] == identity[0]["id"] and value["value"]:
            if (
                not isinstance(value["value"], str)
                or not value["value"].isdigit()
                or str(int(value["value"])) != value["value"]
                or int(value["value"]) <= 0
            ):
                raise ValueError("invalid tracker identity")
            if value["value"] in identities:
                raise ValueError("duplicate tracker identity")
            identities[value["value"]] = value["taskId"]
        if reviews and value["fieldId"] == reviews[0]["id"]:
            if value["taskId"] in review_values:
                raise ValueError("duplicate review field value")
            review_values[value["taskId"]] = value["value"]
    if any(str(row["tmdb_id"]) not in identities for row in rows):
        raise ValueError("review film missing in target project")
    source_titles = {film["tmdb_id"]: film["title"] for film in source["films"]}
    pending, skipped, conflicts = [], 0, holdbacks
    for row in rows:
        task = identities[str(row["tmdb_id"])]
        if task in review_values:
            skipped += 1
        elif call(opener, base, f"/task/{task}")["title"] != source_titles[row["tmdb_id"]]:
            conflicts += 1
        else:
            pending.append(row)
    if not apply:
        return {"pending": len(pending), "skipped": skipped, "conflicts": conflicts, "written": 0}
    if not pending:
        return {"pending": 0, "skipped": skipped, "conflicts": conflicts, "written": 0}
    field_id = reviews[0]["id"] if reviews else ensure_field(opener, base, project, FIELD, "text")
    written = 0
    for row in pending:
        task = identities[str(row["tmdb_id"])]
        if call(opener, base, f"/task/{task}")["title"] != source_titles[row["tmdb_id"]]:
            conflicts += 1
            continue
        current = call(opener, base, f"/custom-field/task/{task}")
        task_identities = [
            item["value"] for item in current if item["fieldId"] == identity[0]["id"]
        ]
        present = [item["value"] for item in current if item["fieldId"] == field_id]
        if task_identities != [str(row["tmdb_id"])] or len(present) > 1:
            raise ValueError("tracker identity or review field changed")
        if present:
            skipped += 1
            continue
        encoded = json.dumps(
            {"schema_version": 1, **row}, ensure_ascii=False, separators=(",", ":")
        )
        call(
            opener,
            base,
            "/custom-field/value",
            {"taskId": task, "fieldId": field_id, "value": encoded},
            "PUT",
        )
        observed = call(opener, base, f"/custom-field/task/{task}")
        if [item["value"] for item in observed if item["fieldId"] == field_id] != [encoded]:
            raise ValueError("review field readback failed; inspect before retry")
        written += 1
    return {"pending": 0, "skipped": skipped, "conflicts": conflicts, "written": written}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--project", required=True)
    auth = parser.add_mutually_exclusive_group(required=True)
    auth.add_argument("--cookie-file", type=Path)
    auth.add_argument(
        "--api-key-env", action="store_true", help="read KANEO_API_KEY from the environment"
    )
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--apply", action="store_true", help="write only empty target fields after preflight"
    )
    args = parser.parse_args()
    base = urlsplit(args.base)
    if base.scheme != "http" or base.hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("only local Kaneo is supported")
    if args.api_key_env:
        opener = api_key_opener(os.environ.get("KANEO_API_KEY"))
    else:
        cookies = http.cookiejar.MozillaCookieJar(str(args.cookie_file))
        cookies.load(ignore_discard=True)
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    result = import_reviews(
        opener,
        args.base.rstrip("/"),
        args.project,
        [json.loads(path.read_text()) for path in args.input],
        json.loads(args.source.read_text()),
        apply=args.apply,
    )
    print(
        f"Pending {result['pending']}; skipped {result['skipped']}; manual-review conflicts {result['conflicts']}; written {result['written']}"
    )


if __name__ == "__main__":
    main()
