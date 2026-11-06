"""Opt-in, bounded local cache population through tracker-scoped endpoints."""

import argparse
import http.cookiejar
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from tmdb_live import approval
from youtrack_client import NoRedirect

ROOT = Path(__file__).resolve().parents[3]
LOCAL = ROOT / ".cache/tracker-poc"
PRIVATE = LOCAL / "private"
MAX_REFRESHES = 25
CACHE_MISS = object()
TASK_ID = re.compile(r"[A-Za-z0-9_-]{1,200}\Z")
ISSUE_ID = re.compile(r"FILMREAL-[1-9][0-9]*\Z")


class BatchError(Exception):
    """A failure with a safe, aggregate-only classification."""

    def __init__(self, kind: str = "error"):
        self.kind = kind


class LocalHTTP:
    def __init__(self, backend: str):
        self.backend = backend
        if backend == "kaneo":
            jar = http.cookiejar.MozillaCookieJar(str(LOCAL / "kaneo-cookies.txt"))
            jar.load(ignore_discard=True)
            self.opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(jar), NoRedirect()
            )
            self.headers = {"Origin": "http://localhost:15174", "Accept": "application/json"}
        elif backend == "youtrack":
            token = (PRIVATE / "youtrack-token").read_text(encoding="utf-8").strip()
            if not token or "\n" in token or "\r" in token:
                raise BatchError("authentication")
            self.opener = urllib.request.build_opener(NoRedirect())
            self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        else:
            raise ValueError("Unknown backend")

    def request(self, base: str, path: str, *, post: bool = False, query=None):
        if base not in {
            "http://localhost:15173/api",
            "http://localhost:15176",
            "http://localhost:18180/api",
        }:
            raise BatchError()
        url = base + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {**self.headers, "Content-Type": "application/json"}
        request = urllib.request.Request(
            url, headers=headers, data=b"{}" if post else None, method="POST" if post else "GET"
        )
        try:
            with self.opener.open(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                try:
                    body = json.load(error)
                except (ValueError, OSError):
                    body = None
                if isinstance(body, dict) and body.get("error") == "Cache miss":
                    return CACHE_MISS
            if error.code == 429:
                raise BatchError("rate_limited") from None
            if error.code in (401, 403):
                raise BatchError("authentication_or_approval") from None
            raise BatchError() from None
        except (urllib.error.URLError, OSError, ValueError, TimeoutError):
            raise BatchError() from None


def identities() -> set[int]:
    data = (PRIVATE / "tmdb-approval/approved-ids.json").read_bytes()
    source = (PRIVATE / "film-input.json").read_bytes()
    watched_preview = (PRIVATE / "tmdb-watched-lookup-preview.md").read_bytes()
    try:
        approval.validate_collection_approval(data, source, watched_preview)
        return approval.parse_allowlist(approval.decode_allowlist(data.decode("utf-8")))
    except (ValueError, TypeError, UnicodeDecodeError):
        raise BatchError("approval") from None


def require_pacing(backend: str, allowed: set[int], kaneo: LocalHTTP, youtrack: LocalHTTP) -> None:
    """Check effective settings through authenticated local-only status endpoints."""
    try:
        selected = json.loads((PRIVATE / "tmdb-pilot-approval/selection.json").read_text())
        ident, issue = selected["tmdb_id"], selected["youtrack_issue"]
        if (
            type(ident) is not int
            or ident not in allowed
            or not isinstance(issue, str)
            or not ISSUE_ID.fullmatch(issue)
        ):
            raise ValueError
        fields = "id,idReadable,project(shortName),customFields(name,value)"
        detail = youtrack.request(
            "http://localhost:18180/api", "/issues/" + issue, query={"fields": fields}
        )
        if issue_identity(detail) != (ident, issue):
            raise ValueError
        kaneo_status = kaneo.request("http://localhost:15176", "/status/config")
        path = f"/issues/{issue}/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/status"
        youtrack_status = youtrack.request("http://localhost:18180/api", path)
        statuses = {"kaneo": kaneo_status, "youtrack": youtrack_status}
        for value in statuses.values():
            if (
                not isinstance(value, dict)
                or set(value) != {"pace_enabled", "refresh_enabled"}
                or any(type(flag) is not bool for flag in value.values())
            ):
                raise ValueError
        active = statuses[backend]
        other = statuses["youtrack" if backend == "kaneo" else "kaneo"]
        if not active["pace_enabled"] or not active["refresh_enabled"] or other["refresh_enabled"]:
            raise ValueError
    except (OSError, ValueError, TypeError, KeyError, BatchError):
        raise BatchError("pacing_not_established") from None


def one(mapping: dict[int, str], ident: int, record: str) -> None:
    if ident in mapping or record in mapping.values():
        raise BatchError("records")
    mapping[ident] = record


def kaneo_records(http: LocalHTTP, allowed: set[int]) -> dict[int, str]:
    project = json.loads((PRIVATE / "kaneo-private-ids.json").read_text())["project"]
    if not isinstance(project, str) or not TASK_ID.fullmatch(project):
        raise BatchError("records")
    base = "http://localhost:15173/api"
    rows = http.request(base, f"/custom-field/project/{project}/values")
    if not isinstance(rows, list):
        raise BatchError("records")
    found: dict[int, str] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("fieldName") != "POC TMDB ID":
            continue
        value = row.get("value")
        if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", value):
            raise BatchError("records")
        ident, task = int(value), row.get("taskId")
        if ident in allowed:
            if not isinstance(task, str) or not TASK_ID.fullmatch(task):
                raise BatchError("records")
            one(found, ident, task)
    if set(found) != allowed:
        raise BatchError("records")
    for ident, task in found.items():
        detail = http.request(base, f"/task/{task}")
        fields = http.request(base, f"/custom-field/task/{task}")
        if not isinstance(detail, dict) or detail.get("id") != task or not isinstance(fields, list):
            raise BatchError("records")
        values = [r for r in fields if isinstance(r, dict) and r.get("fieldName") == "POC TMDB ID"]
        if (
            len(values) != 1
            or values[0].get("taskId") != task
            or values[0].get("fieldType") != "text"
            or values[0].get("value") != str(ident)
        ):
            raise BatchError("records")
    return found


def issue_identity(issue: dict) -> tuple[int, str]:
    if not isinstance(issue, dict) or issue.get("project", {}).get("shortName") != "FILMREAL":
        raise BatchError("records")
    fields = issue.get("customFields")
    if not isinstance(fields, list):
        raise BatchError("records")
    values = [
        f.get("value") for f in fields if isinstance(f, dict) and f.get("name") == "FilmIQ TMDB ID"
    ]
    readable = issue.get("idReadable")
    if (
        len(values) != 1
        or type(values[0]) is not int
        or not isinstance(readable, str)
        or not ISSUE_ID.fullmatch(readable)
    ):
        raise BatchError("records")
    return values[0], readable


def youtrack_records(http: LocalHTTP, allowed: set[int]) -> dict[int, str]:
    base = "http://localhost:18180/api"
    fields = "id,idReadable,project(shortName),customFields(name,value)"
    found: dict[int, str] = {}
    seen: set[str] = set()
    skip = 0
    while True:
        page = http.request(
            base,
            "/issues",
            query={"query": "project: FILMREAL", "fields": fields, "$top": 100, "$skip": skip},
        )
        if not isinstance(page, list):
            raise BatchError("records")
        if not page:
            break
        for issue in page:
            if (
                not isinstance(issue, dict)
                or not isinstance(issue.get("id"), str)
                or issue["id"] in seen
            ):
                raise BatchError("records")
            seen.add(issue["id"])
            ident, readable = issue_identity(issue)
            if ident in allowed:
                one(found, ident, readable)
        skip += len(page)
    if set(found) != allowed:
        raise BatchError("records")
    for ident, issue in found.items():
        detail = http.request(base, "/issues/" + issue, query={"fields": fields})
        if issue_identity(detail) != (ident, issue):
            raise BatchError("records")
    return found


def endpoint(http: LocalHTTP, backend: str, record: str, *, refresh: bool):
    if backend == "kaneo":
        return http.request(
            "http://localhost:15176", f"/{'refresh' if refresh else 'cache'}/{record}"
        )
    action = "read" if refresh else "cached"
    path = f"/issues/{record}/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/{action}"
    return http.request("http://localhost:18180/api", path, post=refresh)


def validate_result(value, ident: int, now: datetime) -> str:
    if (
        not isinstance(value, dict)
        or value.get("tmdb_id") != ident
        or type(value.get("tmdb_id")) is not int
    ):
        raise BatchError("response")
    try:
        expires = datetime.fromisoformat(value["cache_expires_at"].replace("Z", "+00:00"))
        if expires.tzinfo is None or expires <= now:
            raise ValueError
    except (ValueError, TypeError, KeyError, AttributeError):
        raise BatchError("response") from None
    availability = value.get("availability")
    if not isinstance(availability, dict) or availability.get("status") not in (
        "complete",
        "partial",
        "unknown",
    ):
        raise BatchError("response")
    return availability["status"]


def run(http, backend: str, allowed: set[int], report: dict) -> None:
    records = (
        kaneo_records(http, allowed) if backend == "kaneo" else youtrack_records(http, allowed)
    )
    report["validated"] = len(records)
    for ident, record in sorted(records.items()):
        cached = endpoint(http, backend, record, refresh=False)
        if cached is not CACHE_MISS:
            status = validate_result(cached, ident, datetime.now(UTC))
            report[f"availability_{status}"] += 1
            report["skipped_fresh"] += 1
            continue
        if report["refreshed"] >= MAX_REFRESHES:
            break
        report["attempted"] += 1
        fresh = endpoint(http, backend, record, refresh=True)
        validate_result(fresh, ident, datetime.now(UTC))
        cached = endpoint(http, backend, record, refresh=False)
        status = validate_result(cached, ident, datetime.now(UTC))
        report[f"availability_{status}"] += 1
        report["refreshed"] += 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("kaneo", "youtrack"), required=True)
    parser.add_argument("--run", action="store_true", help="explicitly enable provider refreshes")
    args = parser.parse_args()
    report = {
        "validated": 0,
        "skipped_fresh": 0,
        "attempted": 0,
        "refreshed": 0,
        "availability_complete": 0,
        "availability_partial": 0,
        "availability_unknown": 0,
        "result": "error",
    }
    if not args.run:
        report["result"] = "not_started"
        print(json.dumps(report, sort_keys=True))
        return 2
    try:
        allowed = identities()
        clients = {name: LocalHTTP(name) for name in ("kaneo", "youtrack")}
        require_pacing(args.backend, allowed, clients["kaneo"], clients["youtrack"])
        run(clients[args.backend], args.backend, allowed, report)
        report["result"] = "complete" if report["refreshed"] < MAX_REFRESHES else "limit_reached"
    except BatchError as error:
        report["result"] = error.kind
    except (Exception, KeyboardInterrupt):
        report["result"] = "error"
    print(json.dumps(report, sort_keys=True))
    return 0 if report["result"] in ("complete", "limit_reached") else 1


if __name__ == "__main__":
    sys.exit(main())
