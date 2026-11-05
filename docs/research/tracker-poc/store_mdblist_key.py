"""Store an MDBList API key in the ignored project-local POC cache."""

import getpass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESTINATION = ROOT / ".cache/tracker-poc/private/mdblist-key"


def main() -> None:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = getpass.getpass("Paste your MDBList API key (input is hidden): ").strip()
    if not key or "\n" in key or "\r" in key:
        raise SystemExit("Key is empty or malformed; no file was written.")
    fd = os.open(DESTINATION, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(key)
    print("Saved the key in the ignored project-local cache.")


if __name__ == "__main__":
    main()
