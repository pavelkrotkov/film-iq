"""Exercise a single synthetic Kaneo record using an existing local session.

This is an API experiment, not the film application or its acceptance suite.
Only use it against an isolated POC project. No real TMDB ID is created.
"""

import argparse
import http.cookiejar
import json
import urllib.error
import urllib.request
from pathlib import Path


def call(opener, base: str, path: str, payload=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        base + "/api" + path,
        data,
        {"Content-Type": "application/json", "Origin": base},
        method=method,
    )
    with opener.open(request, timeout=30) as response:
        return json.load(response)


def ensure_field(opener, base: str, project: str, name: str, kind: str, options=None):
    fields = call(opener, base, f"/custom-field/project/{project}")
    existing = [field for field in fields if field["name"] == name]
    if len(existing) > 1 or (existing and existing[0]["type"] != kind):
        raise ValueError(f"ambiguous field: {name}")
    if existing:
        return existing[0]["id"]
    payload = {"projectId": project, "name": name, "type": kind}
    if options is not None:
        payload["options"] = options
    return call(opener, base, "/custom-field", payload)["id"]


def matching_tasks(opener, base: str, project: str, field: str):
    values = call(opener, base, f"/custom-field/project/{project}/values")
    return [v["taskId"] for v in values if v["fieldId"] == field and v["value"] == "fixture-0001"]


def run(base: str, project: str, cookie_file: Path):
    cookies = http.cookiejar.MozillaCookieJar(str(cookie_file))
    cookies.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    identifier = ensure_field(opener, base, project, "POC Fixture ID", "text")
    score = ensure_field(opener, base, project, "POC Critic Score", "number")
    streaming = ensure_field(
        opener, base, project, "POC Streaming", "multiselect", ["Netflix", "Hulu"]
    )
    found = matching_tasks(opener, base, project, identifier)
    if len(found) > 1:
        raise ValueError("duplicate synthetic fixture IDs")
    if found:
        task = found[0]
    else:
        task = call(
            opener,
            base,
            f"/task/{project}",
            {
                "title": "Fictional Film 0001",
                "description": "Initial synthetic synopsis.",
                "priority": "no-priority",
                "status": "to-do",
                "customFields": [{"fieldId": identifier, "value": "fixture-0001"}],
            },
        )["id"]
    call(
        opener,
        base,
        f"/task/description/{task}",
        {"description": "Updated synthetic synopsis."},
        "PUT",
    )
    call(opener, base, f"/task/status/{task}", {"status": "in-progress"}, "PUT")
    for field, value in ((score, "8"), (streaming, '["Netflix"]')):
        call(
            opener,
            base,
            "/custom-field/value",
            {"taskId": task, "fieldId": field, "value": value},
            "PUT",
        )
    record = call(opener, base, f"/task/{task}")
    values = {v["fieldId"]: v["value"] for v in call(opener, base, f"/custom-field/task/{task}")}
    assert record["description"] == "Updated synthetic synopsis."
    assert record["status"] == "in-progress"
    assert values[score] == "8" and json.loads(values[streaming]) == ["Netflix"]
    assert matching_tasks(opener, base, project, identifier) == [task]
    try:
        call(
            opener,
            base,
            "/custom-field/value",
            {"taskId": task, "fieldId": score, "value": "not-a-number"},
            "PUT",
        )
    except urllib.error.HTTPError as error:
        assert error.code == 400
    else:
        raise AssertionError("invalid numeric field was accepted")
    try:
        call(
            urllib.request.build_opener(),
            base,
            f"/task/description/{task}",
            {"description": "unauthorized"},
            "PUT",
        )
    except urllib.error.HTTPError as error:
        assert error.code in (401, 403)
    else:
        raise AssertionError("unauthenticated modification was accepted")
    assert call(opener, base, f"/task/{task}")["description"] == "Updated synthetic synopsis."
    print("Kaneo synthetic create/update/readback and unauthenticated rejection passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--project", required=True)
    parser.add_argument("--cookie-file", required=True, type=Path)
    args = parser.parse_args()
    run(args.base.rstrip("/"), args.project, args.cookie_file)
