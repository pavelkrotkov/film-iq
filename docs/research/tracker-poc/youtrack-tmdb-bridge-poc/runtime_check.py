"""Create two fictional FILMPOC issues and check the installed fixture handler.

This accesses only the local YouTrack API. It leaves the new issues in place.
An uncertain issue-creation result must be inspected before retrying.
"""

import json
import secrets
from urllib.error import HTTPError, URLError
from urllib.request import Request

from youtrack_client import BASE_URL, YouTrackClient

APP = "filmiq-tmdb-fixture-isolated"
ALLOWED = (900000001, 900000002)


def field(value):
    return {"name": "FilmIQ TMDB ID", "$type": "SimpleIssueCustomField", "value": value}


def request(client, path, *, authenticated=True, body=None):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if authenticated:
        headers["Authorization"] = "Bearer " + client._token
    req = Request(
        BASE_URL + path,
        data=json.dumps(body).encode() if body is not None else None,
        method="POST" if body is not None else "GET",
        headers=headers,
    )
    try:
        with client._opener.open(req, timeout=25) as response:
            status, response_headers, data = response.status, response.headers, response.read()
    except HTTPError as error:
        status, response_headers, data = error.code, error.headers, error.read()
    except (URLError, OSError, TimeoutError):
        return None, {}, None
    try:
        decoded = json.loads(data) if data else None
    except (ValueError, UnicodeDecodeError):
        decoded = None
    return status, response_headers, decoded


def main():
    client = YouTrackClient()
    project_data = client.request("admin/projects/FILMPOC", query={"fields": "id,shortName"})
    if not isinstance(project_data, dict) or project_data.get("shortName") != "FILMPOC":
        raise RuntimeError("Synthetic project could not be verified")
    project = project_data["id"]
    marker = secrets.token_hex(4)
    issues = []
    for index, ident in enumerate(ALLOWED, 1):
        result = client.request(
            "issues",
            query={"fields": "id,idReadable"},
            body={
                "project": {"id": project},
                "summary": f"SYNTHETIC bridge runtime check {marker} / {index}",
                "description": "Fictional fixture for the isolated metadata bridge; no personal film.",
                "customFields": [field(ident)],
            },
        )
        issue = result.get("idReadable") if isinstance(result, dict) else None
        if not isinstance(issue, str) or not issue.startswith("FILMPOC-"):
            raise RuntimeError("Issue creation outcome uncertain; inspect FILMPOC before retrying")
        issues.append(issue)
        print(f"Created fictional issue: {issue}", flush=True)

    def endpoint(issue):
        return f"issues/{issue}/extensionEndpoints/{APP}/metadata/read"

    failures = []

    def check(label, result, expected):
        status, headers, payload = result
        good = status in expected
        print(f"{label}: HTTP {status}; {'passed' if good else 'FAILED'}", flush=True)
        if not good:
            failures.append(label)
        return headers, payload

    check(
        "Anonymous denial",
        request(client, endpoint(issues[0]), authenticated=False, body={}),
        {401, 403, 404},
    )
    check(
        "Unknown issue denial", request(client, endpoint("FILMPOC-999999999"), body={}), {403, 404}
    )
    headers, payload = check(
        "Fictional metadata", request(client, endpoint(issues[0]), body={}), {200}
    )
    if (
        not isinstance(payload, dict)
        or payload.get("tmdb_id") != ALLOWED[0]
        or payload.get("title") != "Fictional film"
    ):
        failures.append("Fictional response identity")
        print("Fictional response identity: FAILED", flush=True)
    elif "no-store" not in headers.get("Cache-Control", "").lower():
        failures.append("Fictional response cache policy")
        print("Fictional response cache policy: FAILED", flush=True)
    else:
        print("Fictional response identity and no-store: passed", flush=True)
    limit_headers, _ = check(
        "Synthetic rate limit", request(client, endpoint(issues[1]), body={}), {429}
    )
    if "no-store" not in limit_headers.get("Cache-Control", "").lower():
        failures.append("Rate-limit response cache policy")
        print("Rate-limit response cache policy: FAILED", flush=True)
    else:
        print("Rate-limit response no-store: passed", flush=True)

    # The mutated issue is newly created and always restored to the approved fixture value.
    try:
        client.request(f"issues/{issues[0]}", body={"customFields": [field(11)]})
        check("Unapproved fixture ID denial", request(client, endpoint(issues[0]), body={}), {403})
    finally:
        client.request(f"issues/{issues[0]}", body={"customFields": [field(ALLOWED[0])]})
        print("Fictional issue restored to its approved fixture ID", flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} synthetic runtime checks failed")
    print("Signed-in restricted-user visibility and widget invocation remain untested.")


if __name__ == "__main__":
    main()
