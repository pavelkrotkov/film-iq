"""Count local reviewed-catalog results for the existing approved POC records.

This reads only the two local trackers and their catalog endpoints. It makes
no provider requests, changes no records, prints no film identifiers or
titles, and retains no response bodies. Run from the POC worktree root.
"""

import http.cookiejar
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from kaneo_smoke import call
from tmdb_live import approval
from youtrack_client import YouTrackClient

ROOT = Path(__file__).resolve().parents[3]
LOCAL = ROOT / ".cache/tracker-poc"


def main() -> None:
    private = LOCAL / "private"
    manifest = json.loads((private / "film-input.json").read_text(encoding="utf-8"))["films"]
    allowed = approval.parse_allowlist(
        approval.decode_allowlist((private / "tmdb-approval/approved-ids.json").read_text())
    )
    identities = [row["tmdb_id"] for row in manifest]
    if any(type(item) is not int or item not in allowed for item in identities) or len(
        set(identities)
    ) != len(identities):
        raise ValueError("Invalid or unapproved input identities")
    expected = set(identities)
    project = json.loads((private / "kaneo-private-ids.json").read_text())["project"]
    jar = http.cookiejar.MozillaCookieJar(str(LOCAL / "kaneo-cookies.txt"))
    jar.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    rows = call(opener, "http://localhost:15173", f"/custom-field/project/{project}/values")
    kaneo = {}
    for row in rows:
        if row.get("fieldName") != "POC TMDB ID" or not row.get("value"):
            continue
        value = row["value"]
        if not isinstance(value, str) or not value.isascii() or not value.isdigit():
            raise ValueError("Invalid Kaneo identity")
        ident = int(value)
        if ident in kaneo or not isinstance(row.get("taskId"), str):
            raise ValueError("Duplicate or invalid Kaneo record")
        kaneo[ident] = row["taskId"]
    client = YouTrackClient()
    issues = client.pages(
        "issues",
        query={
            "query": "project: FILMREAL",
            "fields": "id,idReadable,project(shortName),customFields(name,value)",
        },
    )
    youtrack = {}
    for issue in issues:
        if issue.get("project", {}).get("shortName") != "FILMREAL":
            raise ValueError("Unexpected YouTrack project")
        fields = [
            f.get("value")
            for f in issue.get("customFields", [])
            if f.get("name") == "FilmIQ TMDB ID"
        ]
        if len(fields) != 1 or type(fields[0]) is not int or fields[0] in youtrack:
            raise ValueError("Invalid or duplicate YouTrack identity")
        readable = issue.get("idReadable")
        if not isinstance(readable, str) or not readable.startswith("FILMREAL-"):
            raise ValueError("Invalid YouTrack record")
        youtrack[fields[0]] = readable
    if set(kaneo) != expected or set(youtrack) != expected:
        raise ValueError("Tracker records do not match the approved input")

    results = {"kaneo": set(), "youtrack": set()}
    for ident in sorted(expected):
        url = "http://localhost:15176/catalog/" + urllib.parse.quote(kaneo[ident], safe="")
        request = urllib.request.Request(url, headers={"Origin": "http://localhost:15174"})
        try:
            with opener.open(request, timeout=15) as response:
                data = json.load(response)
                if (
                    response.headers.get("Cache-Control") != "no-store"
                    or data.get("tmdb_id") != ident
                ):
                    raise ValueError("Invalid Kaneo catalog response")
                results["kaneo"].add(ident)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise ValueError("Kaneo catalog request failed") from None
        path = "issues/" + urllib.parse.quote(youtrack[ident], safe="")
        data = client.request(
            path + "/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/catalog"
        )
        if data.get("status") == "available" and data.get("film", {}).get("tmdb_id") == ident:
            results["youtrack"].add(ident)
        elif data.get("status") != "unknown":
            raise ValueError("Invalid YouTrack catalog response")
    print(
        json.dumps(
            {
                "approved_records": len(expected),
                "kaneo_available": len(results["kaneo"]),
                "youtrack_available": len(results["youtrack"]),
                "available_in_both": len(results["kaneo"] & results["youtrack"]),
                "availability_disagreements": len(results["kaneo"] ^ results["youtrack"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Catalog coverage check failed: {type(error).__name__}", file=sys.stderr)
        raise SystemExit(1) from None
