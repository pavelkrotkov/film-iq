"""Resolve source facts and stage seven-day TMDB metadata for the private library."""

import argparse
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path
from threading import Lock
from types import SimpleNamespace

from film_iq.personal_io import private_json

MATCH_REVIEW = "complete-search-v2"


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
    return json.dumps(
        [
            row.get("tmdb_id"),
            row["raw_title"],
            row.get("year"),
            row.get("director"),
            row.get("imdb_id"),
            row.get("qid") or row.get("wikidata_id"),
            row.get("alternate_titles", []),
        ]
    )


def credited_director(source, credit):
    supplied, credited = name_key(source).split(), name_key(credit).split()
    if not supplied or not credited:
        return False
    if len(supplied) == 1:
        return supplied[0] in (credited[0], credited[-1])
    if supplied[-1] != credited[-1]:
        return False
    return len(supplied) == len(credited) and all(
        given == full or (len(given) == 1 and full.startswith(given))
        for given, full in zip(supplied, credited, strict=True)
    )


def same_work(row, movie):
    titles = {
        name_key(re.sub(r"\s*\(\d{4}\)\s*$", "", row["raw_title"])),
        *(name_key(title) for title in row.get("alternate_titles", [])),
    }
    title_match = bool(titles.intersection({name_key(movie.title), name_key(movie.original_title)}))
    year_match = row.get("year") is None or abs(row["year"] - (movie.year or 0)) <= 1
    if row.get("imdb_id"):
        return (
            movie.imdb_title_url == f"https://www.imdb.com/title/{row['imdb_id']}/"
            and title_match
            and year_match
        )
    if row.get("tmdb_id"):
        return movie.tmdb_id == row["tmdb_id"] and title_match and year_match
    directors = {name_key(name) for name in movie.directors or ()}
    listed = re.split(r"\s+(?:and|&)\s+|/|,\s+(?=[A-Z])", row.get("director") or "")
    director_match = bool(directors.intersection(name_key(name) for name in listed))
    if not director_match and row.get("year") == movie.year and row.get("year") is not None:
        director_match = any(
            credited_director(name, credit) for name in listed for credit in movie.directors or ()
        )
    return director_match and title_match and year_match


def candidate_year_matches(row, candidate):
    year = str(candidate.get("release_date") or "")[:4]
    return not row.get("year") or not year.isdigit() or abs(row["year"] - int(year)) <= 1


def current_catalogue(directory):
    if directory is None:
        return {}
    cache = import_module("tmdb_live_cache")
    read = import_module("tmdb_cache").read_film
    policy = cache.policy_file(directory)
    now = datetime.now(UTC)
    movies = {}
    for path in (directory / "cache").glob("*.json"):
        if not path.stem.isdigit():
            continue
        ident = int(path.stem)
        record = read(
            directory / "cache", policy, ident, now, authority=directory / "authority.json"
        )
        if payload := cache.cached_response(ident, record):
            movies[ident] = SimpleNamespace(**payload)
    return movies


class Catalogue:
    def __init__(self, directory, existing_cache=None):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.provider = import_module("tmdb_readonly")
        self.movie_payload = import_module("tmdb_payload").movie_payload
        self.configuration = self.provider.fetch("configuration")
        self.lock = Lock()
        self.movie_lock = Lock()
        self.last_request = 0.0
        self.movies = {}
        self.existing = current_catalogue(existing_cache)
        self.status = self.directory / "progress.json"
        self.resolved = (
            json.loads(self.status.read_text())["observations"] if self.status.exists() else {}
        )

    def get(self, path, params=None):
        with self.lock:
            delay = 0.25 - (time.monotonic() - self.last_request)
            if delay > 0:
                time.sleep(delay)
            self.last_request = time.monotonic()
        return self.provider.fetch(path, params)

    def cached(self, ident):
        existing = self.existing.get(ident)
        if existing is not None and datetime.fromisoformat(
            existing.cache_expires_at
        ) > datetime.now(UTC):
            return existing
        staged = self.directory / f"{ident}.json"
        if not staged.exists():
            return None
        record = json.loads(staged.read_text())
        if not isinstance(record.get("payload"), dict):
            return None
        if datetime.fromisoformat(record["expires_at"]) <= datetime.now(UTC):
            return None
        return SimpleNamespace(**record["payload"])

    def movie(self, ident):
        with self.movie_lock:
            if ident in self.movies:
                return self.movies[ident]
            if cached := self.cached(ident):
                self.movies[ident] = cached
                return cached
            details = self.get(
                f"movie/{ident}", {"append_to_response": "credits,external_ids,watch/providers"}
            )

            def combined(path, params=None):
                if path == "configuration":
                    return self.configuration
                if path.endswith("/watch/providers"):
                    return details.get("watch/providers")
                if path == f"movie/{ident}":
                    return details
                raise ValueError("Unexpected metadata request")

            result = self.provider.read_movie(ident, get=combined)
            self.movies[ident] = result
            now = datetime.now(UTC)
            private_json(
                self.directory / f"{ident}.json",
                {
                    "checked_at": now.isoformat(),
                    "expires_at": (now + timedelta(days=7)).isoformat(),
                    "payload": self.movie_payload(result),
                },
            )
            return result

    def search(self, title, year):
        parameters = {"query": title, "include_adult": "false"}
        if year:
            parameters["year"] = year
        result = self.get("search/movie", parameters)
        pages, total = result["total_pages"], result["total_results"]
        if not isinstance(pages, int) or not 0 <= pages <= 500:
            raise ValueError("Search cannot be checked completely")
        results = list(result["results"])
        for page in range(2, pages + 1):
            following = self.get("search/movie", {**parameters, "page": page})
            if following["total_pages"] != pages or following["total_results"] != total:
                raise ValueError("Search changed during identity review")
            results.extend(following["results"])
        if len(results) != total or len({item["id"] for item in results}) != total:
            raise ValueError("Search result count is incomplete or duplicated")
        return results

    def candidates(self, row):
        if row.get("tmdb_id"):
            return [self.movie(row["tmdb_id"])]
        titles = {row["raw_title"], *row.get("alternate_titles", [])}
        names = {name_key(title) for title in titles}
        results = {
            item["id"]: item
            for title in sorted(titles)
            for item in self.search(title, row.get("year"))
        }
        # Search proposes candidates; source facts must corroborate each movie.
        return [
            self.movie(candidate["id"])
            for candidate in results.values()
            if candidate_year_matches(row, candidate)
            and names.intersection(
                {name_key(candidate.get("title")), name_key(candidate.get("original_title"))}
            )
        ]

    def previous(self, row, key):
        previous = self.resolved.get(key)
        if (
            not previous
            or not previous.get("tmdb_id")
            or previous.get("match_review") != MATCH_REVIEW
        ):
            return None
        cached = self.cached(previous["tmdb_id"])
        return previous if cached is not None and same_work(row, cached) else None

    def resolve(self, row):
        key = observation_key(row)
        if not row.get("tmdb_id") and not row.get("director"):
            return key, {
                "tmdb_id": None,
                "reason": "Source needs director or identifier corroboration",
            }
        try:
            if previous := self.previous(row, key):
                return key, previous
            candidates = [movie for movie in self.candidates(row) if same_work(row, movie)]
            if len(candidates) != 1:
                return key, {
                    "tmdb_id": None,
                    "reason": "Source facts did not corroborate one returned candidate",
                }
            found = candidates[0]
            imdb = (
                found.imdb_title_url.rstrip("/").rsplit("/", 1)[-1]
                if found.imdb_title_url
                else None
            )
            return key, {
                "tmdb_id": found.tmdb_id,
                "imdb_id": imdb,
                "match_review": MATCH_REVIEW,
                "evidence": f"TMDB movie/{found.tmdb_id}: source title, supplied identifiers or director/year corroborated",
            }
        except (self.provider.TMDbError, OSError, ValueError, KeyError, TypeError) as exc:
            return key, {"tmdb_id": None, "reason": type(exc).__name__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("--poc", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--cache", type=Path, help="Reuse a current authorized TMDB cache read-only"
    )
    args = parser.parse_args()
    sys.path.insert(0, str(args.poc))
    catalogue = Catalogue(args.output, args.cache)
    rows = {
        observation_key(row): row
        for path in args.sources
        for source in json.loads(path.read_text())["sources"]
        for row in source["entries"]
    }
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index, (key, result) in enumerate(pool.map(catalogue.resolve, rows.values()), 1):
            catalogue.resolved[key] = result
            if index % 20 == 0 or index == len(rows):
                private_json(
                    catalogue.status,
                    {"total": len(rows), "processed": index, "observations": catalogue.resolved},
                )
                print(f"Source identities checked {index}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
