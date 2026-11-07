"""Preview or sanitize unedited legacy Kaneo film provenance, never personal preferences.

Run one instance at a time without concurrent edits; Kaneo has no compare-and-swap.
Historical database pages, WAL and backups are not purged by this operation.
"""

import argparse
import http.cookiejar
import json
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from kaneo_private_import import PUBLIC_FIELD_PROVENANCE, PUBLIC_IDENTITY_PROVENANCE, validate
from kaneo_smoke import call

IDENTITY = "POC TMDB ID"
FIELDS = ("POC Identity Provenance", "POC Field Provenance")
PUBLIC = (PUBLIC_IDENTITY_PROVENANCE, PUBLIC_FIELD_PROVENANCE)


def _legacy(film: dict) -> tuple[str, str]:
    original = film["field_provenance"]
    return original.get("tmdb_id", "unknown"), json.dumps(original, ensure_ascii=False)


def migrate(opener, base: str, project: str, manifest: dict, *, apply: bool = False) -> dict:
    validate(manifest)
    definitions = call(opener, base, f"/custom-field/project/{project}")
    field_ids = {}
    for name in (IDENTITY, *FIELDS):
        found = [field for field in definitions if field["name"] == name]
        if len(found) != 1 or found[0]["type"] != "text":
            raise ValueError("missing, ambiguous or incompatible provenance field")
        field_ids[name] = found[0]["id"]
    values = call(opener, base, f"/custom-field/project/{project}/values")
    by_task = {}
    identities = {}
    for row in values:
        task = row["taskId"]
        field = row["fieldId"]
        if field not in field_ids.values():
            continue
        if field in by_task.setdefault(task, {}):
            raise ValueError("duplicate tracker field value")
        by_task[task][field] = row["value"]
        if field == field_ids[IDENTITY] and row["value"]:
            if (
                not isinstance(row["value"], str)
                or not row["value"].isdigit()
                or str(int(row["value"])) != row["value"]
                or int(row["value"]) <= 0
            ):
                raise ValueError("invalid tracker identity")
            if row["value"] in identities:
                raise ValueError("duplicate tracker identity")
            identities[row["value"]] = task
    if any(str(film["tmdb_id"]) not in identities for film in manifest["films"]):
        raise ValueError("source film missing in target project")

    pending = []
    conflicts = already = 0
    for film in manifest["films"]:
        task = identities[str(film["tmdb_id"])]
        current = by_task.get(task, {})
        old = _legacy(film)
        values_now = tuple(current.get(field_ids[name]) for name in FIELDS)
        if any(value not in (old[index], PUBLIC[index]) for index, value in enumerate(values_now)):
            conflicts += 1
        elif values_now == PUBLIC:
            already += 1
        else:
            pending.append((task, str(film["tmdb_id"]), old))
    if not apply:
        return {"pending": len(pending), "already": already, "conflicts": conflicts, "updated": 0}

    updated = 0
    for task, ident, old in pending:
        rows = call(opener, base, f"/custom-field/task/{task}")
        current = {row["fieldId"]: row["value"] for row in rows}
        if len(current) != len(rows) or current.get(field_ids[IDENTITY]) != ident:
            raise ValueError("tracker identity or fields changed")
        values_now = tuple(current.get(field_ids[name]) for name in FIELDS)
        if any(value not in (old[index], PUBLIC[index]) for index, value in enumerate(values_now)):
            conflicts += 1
            continue
        if values_now == PUBLIC:
            already += 1
            continue
        for index, name in enumerate(FIELDS):
            fresh_rows = call(opener, base, f"/custom-field/task/{task}")
            fresh = {row["fieldId"]: row["value"] for row in fresh_rows}
            if len(fresh) != len(fresh_rows) or fresh.get(field_ids[IDENTITY]) != ident:
                raise ValueError("tracker identity or fields changed")
            fresh_values = tuple(fresh.get(field_ids[field]) for field in FIELDS)
            if any(
                value not in (old[number], PUBLIC[number])
                for number, value in enumerate(fresh_values)
            ):
                conflicts += 1
                break
            if fresh_values[index] == PUBLIC[index]:
                continue
            call(
                opener,
                base,
                "/custom-field/value",
                {"taskId": task, "fieldId": field_ids[name], "value": PUBLIC[index]},
                "PUT",
            )
            observed = call(opener, base, f"/custom-field/task/{task}")
            if [row["value"] for row in observed if row["fieldId"] == field_ids[name]] != [
                PUBLIC[index]
            ]:
                raise ValueError("provenance readback failed; inspect before retry")
        else:
            updated += 1
    return {"pending": 0, "already": already, "conflicts": conflicts, "updated": updated}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--project", required=True)
    parser.add_argument("--cookie-file", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--apply", action="store_true", help="apply only exact legacy-value matches"
    )
    args = parser.parse_args()
    base = urlsplit(args.base)
    if base.scheme != "http" or base.hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("only local Kaneo is supported")
    jar = http.cookiejar.MozillaCookieJar(str(args.cookie_file))
    jar.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    result = migrate(
        opener,
        args.base.rstrip("/"),
        args.project,
        json.loads(args.input.read_text()),
        apply=args.apply,
    )
    print(
        f"Pending {result['pending']}; already neutral {result['already']}; conflicts {result['conflicts']}; updated {result['updated']}"
    )


if __name__ == "__main__":
    main()
