"""Verify two synthetic Kaneo users have independent POC preferences."""

import argparse
import http.cookiejar
import json
import urllib.error
import urllib.request
from pathlib import Path

from kaneo_smoke import call

ORIGIN = "http://localhost:15174"


def login(credentials_file: Path):
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    call(
        opener,
        "http://localhost:15173",
        "/auth/sign-in/email",
        json.loads(credentials_file.read_text()),
    )
    return opener


def preference_request(opener, path: str, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        "http://localhost:15175" + path,
        data,
        {"Origin": ORIGIN, "Content-Type": "application/json"},
        method=method,
    )
    with opener.open(request, timeout=15) as response:
        return json.load(response)


def rejected(opener, path: str, method: str, body: dict, status: int):
    try:
        preference_request(opener, path, method, body)
    except urllib.error.HTTPError as error:
        assert error.code == status
    else:
        raise AssertionError(f"request unexpectedly accepted: {path}")


def check(directory: Path):
    ids = json.loads((directory / "kaneo-ids.json").read_text())
    first = login(directory / "kaneo-test-user.json")
    second = login(directory / "kaneo-viewer.json")
    rows = call(first, "http://localhost:15173", f"/custom-field/project/{ids['project']}/values")
    task = next(
        row["taskId"]
        for row in rows
        if row["fieldName"] == "POC Fixture ID" and row["value"] == "fixture-0001"
    )
    user_a = {
        "interest_score": 8,
        "watchlist": True,
        "watched_at": "2026-11-01T00:00:00+00:00",
        "personal_notes": "Synthetic A",
    }
    user_b = {
        "interest_score": 3,
        "watchlist": False,
        "watched_at": None,
        "personal_notes": "Synthetic B",
    }
    preview_a = preference_request(first, "/preview/" + task, "POST", {"preference": user_a})
    assert preview_a["after"] == user_a
    rejected(first, "/preferences/" + task, "PUT", {"preference": user_a}, 400)
    rejected(
        first, "/preview/" + task, "POST", {"preference": {**user_a, "interest_score": 11}}, 400
    )
    rejected(second, "/preview/nonexistenttask", "POST", {"preference": user_b}, 403)
    try:
        preference_request(
            second,
            "/preferences/" + task,
            "PUT",
            {"preference": user_a, "token": preview_a["token"]},
        )
    except urllib.error.HTTPError as error:
        assert error.code == 400
    else:
        raise AssertionError("another user's preview was accepted")
    preference_request(
        first, "/preferences/" + task, "PUT", {"preference": user_a, "token": preview_a["token"]}
    )
    preview_b = preference_request(second, "/preview/" + task, "POST", {"preference": user_b})
    preference_request(
        second, "/preferences/" + task, "PUT", {"preference": user_b, "token": preview_b["token"]}
    )
    assert preference_request(first, "/preferences")["preferences"][task] == user_a
    assert preference_request(second, "/preferences")["preferences"][task] == user_b
    try:
        preference_request(urllib.request.build_opener(), "/preferences")
    except urllib.error.HTTPError as error:
        assert error.code == 403
    else:
        raise AssertionError("unauthenticated preference access was accepted")
    print(
        "Two users' scores, watchlist, watched state and notes remained independent; preview and authentication enforced"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    check(args.directory)
