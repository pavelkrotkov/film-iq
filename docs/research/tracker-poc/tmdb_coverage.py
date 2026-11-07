"""Summarize opt-in TMDB details coverage without retaining response bodies."""

import argparse
import json
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from tmdb_readonly import TMDbError, fetch, release_year


def normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def coverage(films: list[dict[str, Any]], get=fetch, pause=time.sleep) -> dict[str, Any]:
    """Read once per ID; stop on access/rate limits and report counts only."""
    identities = set()
    for film in films:
        identity, title = film.get("tmdb_id"), film.get("title")
        if type(identity) is not int or identity <= 0 or identity in identities:
            raise ValueError("Input has invalid or duplicate film identity")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Input has no source title")
        identities.add(identity)
    counts: Counter[str] = Counter()
    stopped = False
    for film in films:
        try:
            data = get(f"movie/{film['tmdb_id']}", {"append_to_response": "credits"})
        except TMDbError as error:
            counts["failed"] += 1
            if any(f"HTTP {status}" in str(error) for status in (401, 403, 429)):
                stopped = True
                break
        else:
            title = data.get("title")
            if (
                type(data.get("id")) is not int
                or data["id"] != film["tmdb_id"]
                or not isinstance(title, str)
                or not title.strip()
            ):
                counts["invalid_identity"] += 1
            else:
                counts["valid_response"] += 1
                direct_match = normalized(title) == normalized(film["title"])
                original = data.get("original_title")
                original_match = (
                    isinstance(original, str)
                    and bool(original.strip())
                    and normalized(original) == normalized(film["title"])
                )
                counts["title_exact_normalized"] += direct_match
                counts["additional_original_title_matches"] += not direct_match and original_match
                counts["release_year"] += release_year(data.get("release_date")) is not None
                counts["synopsis"] += isinstance(data.get("overview"), str) and bool(
                    data["overview"].strip()
                )
                counts["poster_path"] += isinstance(data.get("poster_path"), str) and bool(
                    data["poster_path"].strip()
                )
                counts["genres"] += isinstance(data.get("genres"), list) and bool(data["genres"])
                credits = data.get("credits")
                crew = credits.get("crew") if isinstance(credits, dict) else None
                counts["director"] += isinstance(crew, list) and any(
                    isinstance(item, dict)
                    and item.get("job") == "Director"
                    and bool(item.get("name"))
                    for item in crew
                )
        pause(0.3)
    return {
        "input_count": len(films),
        "stopped_on_access_or_rate_limit": stopped,
        "counts": dict(counts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Ignored private film manifest")
    parser.add_argument("--live", action="store_true", help="Actually request TMDB details")
    args = parser.parse_args()
    films = json.loads(args.input.read_text(encoding="utf-8"))["films"]
    if not args.live:
        print(f"Prepared {len(films)} IDs; no requests made")
        return
    print(json.dumps(coverage(films), sort_keys=True))


if __name__ == "__main__":
    main()
