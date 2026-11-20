"""Resolve source facts and stage seven-day TMDB metadata for the private library."""

import argparse
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock

from film_iq.personal_io import private_json


def name_key(value):
    normalized = unicodedata.normalize("NFKD", value or "").casefold()
    return " ".join(
        "".join(
            " " if unicodedata.category(char).startswith("P") else char
            for char in normalized
            if not unicodedata.category(char).startswith("M")
        ).split()
    )


def observation_key(row):
    return json.dumps([row.get("tmdb_id"), row["raw_title"], row.get("year"), row.get("director")])


def same_work(row, movie):
    if row.get("imdb_id"):
        return movie.imdb_title_url == f"https://www.imdb.com/title/{row['imdb_id']}/"
    if row.get("tmdb_id"):
        return movie.tmdb_id == row["tmdb_id"] and (
            name_key(row["raw_title"]) in {name_key(movie.title), name_key(movie.original_title)}
            and (row.get("year") is None or abs(row["year"] - (movie.year or 0)) <= 1)
        )
    directors = {name_key(name) for name in movie.directors or ()}
    listed = re.split(r"\s+(?:and|&|/)\s+|,\s+(?=[A-Z])", row.get("director") or "")
    director_match = bool(directors.intersection(name_key(name) for name in listed))
    return (
        director_match
        and name_key(row["raw_title"]) in {name_key(movie.title), name_key(movie.original_title)}
        and (row.get("year") is None or abs(row["year"] - (movie.year or 0)) <= 1)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("--poc", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.poc))
    from tmdb_payload import movie_payload
    from tmdb_readonly import TMDbError, fetch, read_movie

    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    configuration = fetch("configuration")
    lock = Lock()
    last_request = 0.0
    movies = {}
    resolved = {}
    status = args.output / "progress.json"
    if status.exists():
        resolved = json.loads(status.read_text())["observations"]

    def get(path, params=None):
        nonlocal last_request
        with lock:
            delay = 0.25 - (time.monotonic() - last_request)
            if delay > 0:
                time.sleep(delay)
            last_request = time.monotonic()
        return fetch(path, params)

    def movie(ident):
        if ident in movies:
            return movies[ident]
        staged = args.output / f"{ident}.json"
        details = get(
            f"movie/{ident}", {"append_to_response": "credits,external_ids,watch/providers"}
        )

        def combined(path, params=None):
            if path == "configuration":
                return configuration
            if path.endswith("/watch/providers"):
                return details.get("watch/providers")
            if path == f"movie/{ident}":
                return details
            raise ValueError("Unexpected metadata request")

        result = read_movie(ident, get=combined)
        movies[ident] = result
        now = datetime.now(UTC)
        private_json(
            staged,
            {
                "checked_at": now.isoformat(),
                "expires_at": (now + timedelta(days=7)).isoformat(),
                "payload": movie_payload(result),
            },
        )
        return result

    def resolve(row):
        key = observation_key(row)
        previous = resolved.get(key)
        if (
            previous
            and previous.get("tmdb_id")
            and (args.output / f"{previous['tmdb_id']}.json").exists()
        ):
            return key, previous
        try:
            if row.get("tmdb_id"):
                candidate = movie(row["tmdb_id"])
                candidates = [candidate] if same_work(row, candidate) else []
            else:
                result = get("search/movie", {"query": row["raw_title"], "include_adult": "false"})
                if result.get("total_pages", 0) > 1:
                    return key, {"tmdb_id": None, "reason": "Multiple search pages require review"}
                candidates = []
                for candidate in result.get("results", []):
                    if name_key(row["raw_title"]) not in {
                        name_key(candidate.get("title")),
                        name_key(candidate.get("original_title")),
                    }:
                        continue
                    found = movie(candidate["id"])
                    if same_work(row, found):
                        candidates.append(found)
            if len(candidates) != 1:
                return key, {"tmdb_id": None, "reason": "No unique corroborated film match"}
            found = candidates[0]
            return key, {
                "tmdb_id": found.tmdb_id,
                "imdb_id": found.imdb_title_url.rstrip("/").rsplit("/", 1)[-1]
                if found.imdb_title_url
                else None,
                "evidence": f"TMDB movie/{found.tmdb_id}: source title, supplied identifiers or director/year corroborated",
            }
        except (TMDbError, OSError, ValueError, KeyError, TypeError) as exc:
            return key, {"tmdb_id": None, "reason": type(exc).__name__}

    rows = {}
    for path in args.sources:
        for source in json.loads(path.read_text())["sources"]:
            for row in source["entries"]:
                rows[observation_key(row)] = row
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index, (key, result) in enumerate(pool.map(resolve, rows.values()), 1):
            resolved[key] = result
            if index % 20 == 0 or index == len(rows):
                private_json(
                    status, {"total": len(rows), "processed": index, "observations": resolved}
                )
                print(f"Source identities checked {index}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
