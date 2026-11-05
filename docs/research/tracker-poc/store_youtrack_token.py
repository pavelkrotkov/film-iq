"""Store a user-provided YouTrack POC token in the ignored project cache."""

import argparse
import getpass
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESTINATION = ROOT / ".cache/tracker-poc/private/youtrack-token"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace", action="store_true", help="replace the existing locally stored token"
    )
    args = parser.parse_args()
    DESTINATION.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    token = getpass.getpass("Paste the YouTrack POC token (input is hidden): ").strip()
    if not token or "\n" in token or "\r" in token:
        raise SystemExit("Token is empty or malformed; no file was written.")
    if args.replace:
        request = urllib.request.Request(
            "http://localhost:18180/api/users/me?fields=login",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                user = json.load(response)
        except (OSError, ValueError, urllib.error.URLError):
            raise SystemExit(
                "Could not validate the replacement token; the old file was kept."
            ) from None
        if not isinstance(user, dict) or user.get("login") != "admin":
            raise SystemExit("The replacement is not a local admin token; the old file was kept.")
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if args.replace else os.O_EXCL)
    fd = os.open(DESTINATION, flags, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(token)
    print(f"Saved the token locally at {DESTINATION}")


if __name__ == "__main__":
    main()
