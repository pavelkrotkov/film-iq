"""Store a user-provided YouTrack POC token in the ignored project cache."""

import getpass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESTINATION = ROOT / ".cache/tracker-poc/private/youtrack-token"


def main() -> None:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    token = getpass.getpass("Paste the YouTrack POC token (input is hidden): ").strip()
    if not token or "\n" in token or "\r" in token:
        raise SystemExit("Token is empty or malformed; no file was written.")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(DESTINATION, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(token)
    print(f"Saved the token locally at {DESTINATION}")


if __name__ == "__main__":
    main()
