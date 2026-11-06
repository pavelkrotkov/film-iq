"""Optional loopback TMDB reader with a separately enabled local cache.

The default read-through does not store responses; the opt-in cache retains
normalized metadata under its local policy. Credentials stay in the process
environment. This POC is not a source-rights certification.
"""

import json
import os
import re
import sys
import urllib.error
from importlib import import_module
from pathlib import Path
from urllib.parse import quote

from preferences import current_user, upstream
from reviewed_catalog import catalog_facts
from tmdb_payload import movie_payload
from tmdb_readonly import (
    TMDbError,
    TMDbRateLimited,
    configured_reader,
    configured_refresh_enabled,
    read_movie,
)
from waitress import serve

ALLOWED_ORIGINS = {"http://localhost:15174"}
sys.path.append(str(Path(__file__).resolve().parent / "youtrack-tmdb-live-bridge"))
approval = import_module("live_bridge")


def load_allowlist():
    directory = os.environ.get("FILMIQ_APPROVAL_DIR")
    if not directory:
        raise ValueError("Approval configuration unavailable")
    path = Path(directory) / "approved-ids.json"
    return approval.decode_allowlist(path.read_text(encoding="utf-8"))


def load_catalog_allowlist():
    directory = os.environ.get("FILMIQ_CATALOG_APPROVAL_DIR")
    if directory is None:
        return None
    if not directory:
        raise ValueError("Catalog approval configuration unavailable")
    path = Path(directory) / "approved-ids.json"
    return approval.decode_allowlist(path.read_text(encoding="utf-8"))


def response(start, status: str, payload: dict, origin: str):
    body = json.dumps(payload).encode()
    headers = [
        ("Content-Type", "application/json"),
        ("Cache-Control", "no-store"),
        ("Vary", "Origin"),
        ("Content-Length", str(len(body))),
    ]
    if origin in ALLOWED_ORIGINS:
        headers.append(("Access-Control-Allow-Origin", origin))
        headers.append(("Access-Control-Allow-Credentials", "true"))
    start(status, headers)
    return [body]


def reviewed_catalog_path() -> Path | None:
    value = os.environ.get("FILMIQ_REVIEWED_CATALOG", "")
    path = Path(value) if value else None
    return path if path and path.is_absolute() else None


def app(
    reader=read_movie,
    authenticate=current_user,
    load_approval=load_allowlist,
    get_upstream=upstream,
    load_catalog_path=reviewed_catalog_path,
    read_catalog=catalog_facts,
    cache=None,
    load_catalog_approval=load_catalog_allowlist,
    refresh_enabled=True,
    pace_enabled=False,
):
    def application(environ: dict, start):
        origin = environ.get("HTTP_ORIGIN", "")
        if origin not in ALLOWED_ORIGINS:
            return response(start, "403 Forbidden", {"error": "Origin not allowed"}, origin)
        path = environ.get("PATH_INFO", "").split("/")
        if environ.get("REQUEST_METHOD") != "GET" or len(path) != 3:
            return response(start, "404 Not Found", {"error": "Not found"}, origin)
        is_movie = (
            path[1] == "movie"
            and path[2].isascii()
            and path[2].isdigit()
            and len(path[2]) <= 10
            and 0 < int(path[2]) <= 2_147_483_647
        )
        is_catalog = path[1] == "catalog" and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,200}", path[2]))
        is_cache = path[1] == "cache" and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,200}", path[2]))
        is_refresh = path[1] == "refresh" and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,200}", path[2]))
        is_status = path[1] == "status" and path[2] == "config"
        if not (is_movie or is_catalog or is_cache or is_refresh or is_status):
            return response(start, "404 Not Found", {"error": "Not found"}, origin)
        try:
            authenticate(environ)
        except (PermissionError, OSError, ValueError):
            return response(start, "401 Unauthorized", {"error": "Kaneo session required"}, origin)
        if is_status:
            return response(
                start,
                "200 OK",
                {"pace_enabled": pace_enabled, "refresh_enabled": refresh_enabled},
                origin,
            )
        try:
            catalog_approval = load_catalog_approval() if is_catalog else None
            allowed = approval.parse_allowlist(
                catalog_approval if catalog_approval is not None else load_approval()
            )
        except (OSError, ValueError, TypeError):
            return response(
                start,
                "503 Service Unavailable",
                {"error": "Approval configuration unavailable"},
                origin,
            )
        if (is_movie and cache is not None) or (is_refresh and cache is None):
            return response(start, "404 Not Found", {"error": "Not found"}, origin)
        if is_catalog or is_cache or is_refresh:
            unavailable = {"error": "Reviewed catalog unavailable"}
            cookie = environ.get("HTTP_COOKIE", "")
            try:
                task_id = quote(path[2], safe="")
                task = get_upstream("/task/" + task_id, cookie)
                rows = get_upstream("/custom-field/task/" + task_id, cookie)
            except urllib.error.HTTPError as error:
                if error.code in (401, 403, 404):
                    return response(start, "404 Not Found", unavailable, origin)
                return response(
                    start, "503 Service Unavailable", {"error": "Kaneo unavailable"}, origin
                )
            except (urllib.error.URLError, OSError, ValueError, TypeError):
                return response(
                    start, "503 Service Unavailable", {"error": "Kaneo unavailable"}, origin
                )
            if (
                not isinstance(task, dict)
                or task.get("id") != path[2]
                or not isinstance(rows, list)
            ):
                return response(start, "404 Not Found", unavailable, origin)
            title = task.get("title")
            fields = [
                row
                for row in rows
                if isinstance(row, dict) and row.get("fieldName") == "POC TMDB ID"
            ]
            if (
                not isinstance(title, str)
                or not title.strip()
                or len(fields) != 1
                or fields[0].get("taskId") != path[2]
                or fields[0].get("fieldType") != "text"
            ):
                return response(start, "404 Not Found", unavailable, origin)
            value = fields[0].get("value")
            if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", value):
                return response(start, "404 Not Found", unavailable, origin)
            identity = int(value)
            if identity > 2_147_483_647 or identity not in allowed:
                return response(start, "404 Not Found", unavailable, origin)
            if is_cache:
                if cache is None:
                    return response(start, "404 Not Found", {"error": "Cache unavailable"}, origin)
                try:
                    value = cache.get(identity)
                except (OSError, ValueError, TypeError):
                    return response(
                        start, "503 Service Unavailable", {"error": "Cache unavailable"}, origin
                    )
                return (
                    response(start, "200 OK", value, origin)
                    if value
                    else response(start, "404 Not Found", {"error": "Cache miss"}, origin)
                )
            if is_catalog:
                facts = read_catalog(load_catalog_path(), identity, title)
                return (
                    response(start, "200 OK", facts, origin)
                    if facts is not None
                    else response(start, "404 Not Found", unavailable, origin)
                )
            movie_id = identity
        else:
            movie_id = int(path[2])
            if movie_id not in allowed:
                return response(start, "403 Forbidden", {"error": "Film not approved"}, origin)
        if not refresh_enabled:
            return response(
                start,
                "503 Service Unavailable",
                {"error": "Live refresh temporarily paused"},
                origin,
            )
        if cache is not None:
            try:
                cache.check()
            except (OSError, ValueError, TypeError):
                return response(
                    start, "503 Service Unavailable", {"error": "Cache unavailable"}, origin
                )
        try:
            movie = reader(movie_id)
            if type(movie.tmdb_id) is not int or movie.tmdb_id != movie_id:
                raise ValueError("Response identity mismatch")
        except TMDbRateLimited:
            return response(
                start, "429 Too Many Requests", {"error": "TMDB rate limit reached"}, origin
            )
        except (TMDbError, ValueError, OSError):
            return response(start, "502 Bad Gateway", {"error": "TMDB unavailable"}, origin)
        payload = movie_payload(movie)
        if cache is not None:
            try:
                payload = cache.put(payload)
            except (OSError, ValueError, TypeError, KeyError):
                return response(
                    start, "503 Service Unavailable", {"error": "Cache unavailable"}, origin
                )
        return response(start, "200 OK", payload, origin)

    return application


if __name__ == "__main__":
    cache = None
    stop_purge = None
    if os.environ.get("FILMIQ_TMDB_CACHE_ENABLE", "0") != "0":
        from tmdb_live_cache import from_env, start_purge_worker

        cache = from_env(os.environ)
        stop_purge = start_purge_worker(cache)
    try:
        reader = configured_reader(os.environ)
        refresh_enabled = configured_refresh_enabled(os.environ)
        serve(
            app(
                reader=reader,
                cache=cache,
                refresh_enabled=refresh_enabled,
                pace_enabled=os.environ.get("FILMIQ_TMDB_PACE", "0") == "1",
            ),
            host="127.0.0.1",
            port=15176,
        )
    finally:
        if stop_purge:
            stop_purge()
