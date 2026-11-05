"""Optional command bridge to Movary's own rating service, without SQL or login."""

import json
import subprocess


def parse_rating(value: str, action: str, enabled: bool) -> int | None:
    if action != "rated-watched" or not value:
        return None
    rating = int(value)
    if not 1 <= rating <= 10:
        raise ValueError("Enjoyment rating must be 1–10")
    if not enabled:
        raise ValueError("The rating bridge is not configured")
    return rating


def write_rating(command: list[str], username: str, tmdb_id: int, rating: int) -> None:
    # Values travel on stdin, never in a shell command or process-list argument.
    payload = {"username": username, "tmdb_id": tmdb_id, "rating": rating}
    result = subprocess.run(
        command,
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=60,
    )
    if json.loads(result.stdout) != {"tmdb_id": tmdb_id, "rating": rating}:
        raise ValueError("Movary rating readback failed")
