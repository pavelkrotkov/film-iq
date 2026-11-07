"""Exercise a fictional cache with the two existing local tracker adapters.

Each run creates and leaves one fictional film in the dedicated Kaneo fixture
project and one in YouTrack FILMPOC. The film source is deterministic and
performs no provider requests. The cache is a temporary project-local fixture;
the view projection is test-only and is not a deployed cache bridge.
"""

import argparse
import http.cookiejar
import json
import secrets
import subprocess
import sys
import tempfile
import urllib.request
from datetime import timedelta
from pathlib import Path

from cache_vertical_check import (
    FIXTURES,
    POLICY,
    ROOT,
    START,
    FailedSource,
    PartialSource,
    fixture_payload,
)
from enrichment import FixtureSource, enrich
from kaneo_enrich import KaneoBackend
from kaneo_smoke import call
from tmdb_cache import initialize_authority, write_film
from youtrack_client import YouTrackClient
from youtrack_enrich import YouTrackFixtureBackend, custom_value


def main(directory: Path) -> None:
    directory = directory.resolve()
    if not directory.is_relative_to(FIXTURES.resolve()):
        raise ValueError("Expected a project-local fictional fixture directory")
    local = json.loads((directory / "fictional-editor-test.json").read_text())
    project = local["project"]
    cookies = http.cookiejar.MozillaCookieJar(str(directory / "fictional-cookies.txt"))
    cookies.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    details = call(opener, "http://localhost:15173", f"/project/{project}")
    if details.get("id") != project or not any(
        word in str(details.get("name", "")).lower() for word in ("fictional", "synthetic")
    ):
        raise ValueError("Dedicated fictional Kaneo project could not be confirmed")
    kaneo = KaneoBackend("http://localhost:15173", project, directory / "fictional-cookies.txt")
    youtrack = YouTrackFixtureBackend(YouTrackClient())
    kaneo_rows = call(opener, "http://localhost:15173", f"/custom-field/project/{project}/values")
    kaneo_ids = {row["value"] for row in kaneo_rows if row["fieldId"] == kaneo.fields["identity"]}
    issues = youtrack.issues()
    youtrack_ids = {custom_value(issue, "FilmIQ Fixture ID") for issue in issues}
    ident = 1_000_000_000 + secrets.randbelow(1_000_000_000)
    while str(ident) in kaneo_ids or ident in youtrack_ids:
        ident = 1_000_000_000 + secrets.randbelow(1_000_000_000)

    FIXTURES.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix="fictional-live-cache-", dir=FIXTURES) as location:
        root = Path(location)
        views = []
        for index, backend in enumerate((kaneo, youtrack)):
            cache, authority = root / f"cache-{index}", root / f"authority-{index}.json"
            initialize_authority(cache, authority, POLICY, START)
            record = enrich(FixtureSource(), backend, ident, START)
            write_film(
                cache,
                POLICY,
                fixture_payload(FixtureSource(), START, ident),
                START,
                START,
                authority=authority,
            )
            if index == 0:
                call(
                    opener,
                    "http://localhost:15173",
                    f"/task/description/{record}",
                    {"description": "User fictional synopsis"},
                    "PUT",
                )
                kaneo._set(record, kaneo.fields["genre"], "User fictional genre")

                def observation(record_id=record):
                    rows = call(opener, "http://localhost:15173", f"/custom-field/task/{record_id}")
                    return next(
                        row["value"]
                        for row in rows
                        if row["fieldId"] == kaneo.fields["availability"]
                    )
            else:
                youtrack.client.request(
                    f"issues/{record}",
                    body={
                        "description": "User fictional synopsis",
                        "customFields": [
                            {
                                "name": "FilmIQ Genre",
                                "$type": "SimpleIssueCustomField",
                                "value": "User fictional genre",
                            }
                        ],
                    },
                )

                def observation(record_id=record):
                    issue = youtrack.client.request(
                        f"issues/{record_id}",
                        query={"fields": "id,description,customFields(name,value)"},
                    )
                    return custom_value(issue, "FilmIQ Provider Observation")

            previous = observation()
            assert enrich(FixtureSource(), backend, ident, START) == record
            later = START + timedelta(days=1)
            assert enrich(PartialSource(), backend, ident, later) == record
            write_film(
                cache,
                POLICY,
                fixture_payload(PartialSource(), later, ident),
                later,
                later,
                authority=authority,
            )
            try:
                enrich(FailedSource(), backend, ident, later)
            except RuntimeError:
                pass
            else:
                raise AssertionError("Fictional provider failure was not surfaced")
            assert observation() == previous
            if index == 0:
                task = call(opener, "http://localhost:15173", f"/task/{record}")
                values = call(opener, "http://localhost:15173", f"/custom-field/task/{record}")
                assert task["description"] == "User fictional synopsis"
                assert (
                    next(row["value"] for row in values if row["fieldId"] == kaneo.fields["genre"])
                    == "User fictional genre"
                )
            else:
                issue = youtrack.client.request(
                    f"issues/{record}", query={"fields": "id,description,customFields(name,value)"}
                )
                assert issue["description"] == "User fictional synopsis"
                assert custom_value(issue, "FilmIQ Genre") == "User fictional genre"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "docs/research/tracker-poc/cache_vertical_check.py"),
                    "--read-fixture",
                    str(cache),
                    str(authority),
                    str(ident),
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=True,
            )
            views.append(json.loads(result.stdout))
        result = subprocess.run(
            ["node", str(ROOT / "docs/research/tracker-poc/ui/cache_vertical_view_check.mjs")],
            input=json.dumps(views),
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        assert "Fictional cache view filters passed" in result.stdout
    print(
        "Two fictional tracker records passed repeat, user-edit, failure and fresh-process cache checks"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kaneo-fixture-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        main(args.kaneo_fixture_dir)
    except Exception as error:
        print(f"Fictional live check failed: {type(error).__name__}", file=sys.stderr)
        raise SystemExit(1) from None
