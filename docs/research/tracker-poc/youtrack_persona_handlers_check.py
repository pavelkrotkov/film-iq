"""Verify installed app handlers using two existing fictional users and FILMPOC.

Pass two temporary user-token file paths from the ignored project-local cache.
The script refuses non-POC logins and existing watched snapshots. It creates
synthetic personal preferences and one synthetic watched snapshot in app-owned
properties; those test values remain after the run. No private film is read.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from youtrack_client import ROOT, NoRedirect

BASE = "http://localhost:18180/api/"
APP = "extensionEndpoints/filmiq-poc/"


class Client:
    def __init__(self, token_file: Path | None):
        self.token = token_file.read_text(encoding="utf-8").strip() if token_file else None
        self.opener = build_opener(NoRedirect())

    def call(self, path: str, *, query: dict | None = None, body: dict | None = None):
        url = BASE + path + ("?" + urlencode(query) if query else "")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(url, headers=headers, data=json.dumps(body).encode() if body else None)
        try:
            with self.opener.open(request, timeout=20) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, None


def expect(client: Client, path: str, status: int, *, query=None, body=None):
    actual, value = client.call(path, query=query, body=body)
    if actual != status:
        raise RuntimeError(f"Unexpected HTTP {actual} for {path}; expected {status}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-a", required=True, type=Path)
    parser.add_argument("--token-b", required=True, type=Path)
    args = parser.parse_args()
    users = [Client(args.token_a), Client(args.token_b)]
    known = json.loads((ROOT / ".cache/tracker-poc/private/youtrack-personas.json").read_text())
    logins = [expect(user, "users/me", 200, query={"fields": "login"})["login"] for user in users]
    if len(set(logins)) != 2 or set(logins) != set(known):
        raise RuntimeError("Tokens must belong to the two existing fictional POC accounts")
    anonymous = Client(None)
    expect(anonymous, APP + "preferences/all", 401)
    expect(anonymous, APP + "movary/watched", 401, query={"project": "FILMPOC"})
    for user in users:
        state = expect(user, APP + "movary/watched", 200, query={"project": "FILMPOC"})
        if state.get("status") != "unknown" or state.get("films") != {}:
            raise RuntimeError(
                "A fictional account already has a watched snapshot; refusing replacement"
            )
    selected = None
    for number in range(1, 31):
        issue = f"FILMPOC-{number}"
        results = [
            user.call(APP + "preferences/preference", query={"issue_id": issue}) for user in users
        ]
        if all(status == 200 and value.get("recorded") is False for status, value in results):
            selected = issue
            break
    if selected is None:
        raise RuntimeError("No shared unused fictional issue was found")
    expect(users[0], APP + "preferences/preference", 404, query={"issue_id": "FILMPOC-999999"})
    a = {
        "interest_score": 9,
        "watchlist": True,
        "watched_at": "2020-01-01T00:00:00.000Z",
        "personal_notes": "Fictional A",
    }
    b = {
        "interest_score": 3,
        "watchlist": False,
        "watched_at": None,
        "personal_notes": "Fictional B",
    }
    preview = expect(
        users[0], APP + "preferences/preview", 200, body={"issue_id": selected, "preference": a}
    )
    if preview != {"issue_id": selected, "before": None, "after": a}:
        raise RuntimeError("Fictional preview did not match the proposed preference")
    expect(users[1], APP + "preferences/confirm", 409, body=preview)
    expect(users[0], APP + "preferences/confirm", 200, body=preview)
    expect(users[0], APP + "preferences/confirm", 409, body=preview)
    preview = expect(
        users[1], APP + "preferences/preview", 200, body={"issue_id": selected, "preference": b}
    )
    expect(users[1], APP + "preferences/confirm", 200, body=preview)
    for user, value in zip(users, (a, b), strict=True):
        result = expect(user, APP + "preferences/preference", 200, query={"issue_id": selected})
        if result.get("preference") != value:
            raise RuntimeError("Synthetic preference readback did not match")
    snapshot = {
        "version": "youtrack-poc-movary-watched-v1",
        "source": "Movary",
        "complete": True,
        "observed_at": datetime.now(UTC).isoformat(),
        "project": "FILMPOC",
        "films": {
            selected: {
                "watched": True,
                "played_watch_dates": [{"date": None, "plays": 2}],
                "history_export_dates": [None],
            }
        },
    }
    expect(users[0], APP + "movary/import", 200, body=snapshot)
    one = expect(users[0], APP + "movary/watched", 200, query={"project": "FILMPOC"})
    two = expect(users[1], APP + "movary/watched", 200, query={"project": "FILMPOC"})
    if (
        one.get("films") != snapshot["films"]
        or two.get("status") != "unknown"
        or two.get("films") != {}
    ):
        raise RuntimeError("Synthetic watched snapshots were not isolated")
    for user, value in zip(users, (a, b), strict=True):
        if (
            expect(user, APP + "preferences/preference", 200, query={"issue_id": selected}).get(
                "preference"
            )
            != value
        ):
            raise RuntimeError("Synthetic watched import changed preferences")
    print(
        "Two fictional users: independent preferences, preview protection, anonymous denial and watched isolation passed"
    )


if __name__ == "__main__":
    main()
