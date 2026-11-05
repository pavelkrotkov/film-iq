"""Opt-in YouTrack TMDB bridge; the allowlist is revalidated on every request."""

import hmac
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from wsgiref.simple_server import WSGIRequestHandler, make_server

from tmdb_payload import movie_payload
from tmdb_readonly import TMDbRateLimited, read_movie

DESTINATIONS = frozenset({"api.themoviedb.org", "image.tmdb.org"})
ALLOWLIST_PATH = Path("/run/filmiq/approval/approved-ids.json")


@dataclass(frozen=True)
class Config:
    bridge_token: str = field(repr=False)


def parse_allowlist(value: object) -> frozenset[int]:
    if not isinstance(value, dict):
        raise ValueError("Invalid allowlist")
    required = {"version", "allowed_ids", "destinations"}
    optional = {"watched_approval_preview_sha256", "source_manifest_sha256"}
    if not required <= value.keys() or value.keys() - required - optional:
        raise ValueError("Invalid allowlist")
    ids, destinations = value["allowed_ids"], value["destinations"]
    if (
        type(value["version"]) is not int
        or value["version"] != 1
        or not isinstance(ids, list)
        or not ids
        or any(type(item) is not int or not 0 < item <= 2147483647 for item in ids)
        or len(set(ids)) != len(ids)
        or not isinstance(destinations, list)
        or len(destinations) != len(DESTINATIONS)
        or any(not isinstance(item, str) for item in destinations)
        or set(destinations) != DESTINATIONS
        or any(
            not isinstance(value[k], str) or not value[k].strip() for k in optional & value.keys()
        )
    ):
        raise ValueError("Invalid allowlist")
    return frozenset(ids)


def decode_allowlist(raw: str) -> object:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Invalid allowlist")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=unique)


def config_from_env(env: Mapping[str, str]) -> Config:
    token = env.get("FILMIQ_BRIDGE_TOKEN", "")
    tmdb = env.get("TMDB_READ_ACCESS_TOKEN") or env.get("TMDB_API_KEY", "")
    if (
        env.get("FILMIQ_TMDB_BRIDGE_ENABLE_LIVE") != "1"
        or not token.isascii()
        or len(token) < 32
        or token != token.strip()
        or any(c.isspace() for c in token)
        or not tmdb
        or tmdb != tmdb.strip()
        or any(c.isspace() for c in tmdb)
    ):
        raise ValueError("Live bridge configuration unavailable")
    return Config(token)


def safe_poster(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        if (
            url.scheme == "https"
            and url.hostname == "image.tmdb.org"
            and url.port is None
            and url.username is None
            and url.password is None
            and not url.query
            and not url.fragment
        ):
            return value
    except ValueError:
        pass
    return None


def app(
    config: Config,
    load_allowlist: Callable[[], object],
    reader: Callable,
    catalog_reader=None,
    cache=None,
):
    """The reader is injected so tests can never accidentally use live fetch."""

    def application(environ, start):
        def send(code, value):
            body = json.dumps(value).encode()
            start(
                code,
                [
                    ("Content-Type", "application/json"),
                    ("Cache-Control", "no-store"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        auth = environ.get("HTTP_AUTHORIZATION", "")
        if (
            not isinstance(auth, str)
            or not auth.isascii()
            or not hmac.compare_digest(auth, "Bearer " + config.bridge_token)
        ):
            return send("401 Unauthorized", {"error": "Unauthorized"})
        path = environ.get("PATH_INFO")
        if environ.get("REQUEST_METHOD") != "POST" or path not in {
            "/metadata",
            "/catalog",
            "/cache",
        }:
            return send("404 Not Found", {"error": "Not found"})
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
            if not 0 < length <= 2048:
                raise ValueError("Invalid request")
            value = json.loads(environ["wsgi.input"].read(length))
            expected = {"tmdb_id", "title"} if path == "/catalog" else {"tmdb_id"}
            if not isinstance(value, dict) or set(value) != expected:
                raise ValueError("Invalid request")
            ident = value["tmdb_id"]
            if type(ident) is not int or not 0 < ident <= 2147483647:
                raise ValueError("Invalid request")
            if path == "/catalog" and (
                not isinstance(value["title"], str)
                or not value["title"].strip()
                or len(value["title"]) > 500
            ):
                raise ValueError("Invalid request")
        except (ValueError, UnicodeDecodeError):
            return send("400 Bad Request", {"error": "Invalid request"})
        try:
            allowed = parse_allowlist(load_allowlist())
        except (OSError, ValueError, TypeError):
            return send("503 Service Unavailable", {"error": "Approval configuration unavailable"})
        if ident not in allowed:
            return send("403 Forbidden", {"error": "Film not approved"})
        if path == "/cache":
            if cache is None:
                return send("404 Not Found", {"error": "Cache unavailable"})
            try:
                value = cache.get(ident)
            except (OSError, ValueError, TypeError):
                return send("503 Service Unavailable", {"error": "Cache unavailable"})
            return (
                send("200 OK", value) if value else send("404 Not Found", {"error": "Cache miss"})
            )
        if path == "/catalog":
            try:
                facts = catalog_reader(ident, value["title"]) if catalog_reader else None
            except (OSError, ValueError, TypeError, KeyError):
                return send("503 Service Unavailable", {"error": "Reviewed catalog unavailable"})
            return send(
                "200 OK", {"status": "available", "film": facts} if facts else {"status": "unknown"}
            )
        if cache is not None:
            try:
                cache.check()
            except (OSError, ValueError, TypeError):
                return send("503 Service Unavailable", {"error": "Cache unavailable"})
        try:
            movie = reader(ident)
            if type(movie.tmdb_id) is not int or movie.tmdb_id != ident:
                raise ValueError("Response identity mismatch")
            payload = movie_payload(movie)
            payload["poster_url"] = safe_poster(payload["poster_url"])
            if cache is not None:
                payload["cache_expires_at"] = cache.put(payload)["cache_expires_at"]
        except TMDbRateLimited:
            return send("429 Too Many Requests", {"error": "TMDB rate limit reached"})
        except Exception:
            return send("502 Bad Gateway", {"error": "TMDB unavailable"})
        return send("200 OK", payload)

    return application


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def main():
    import os

    try:
        config = config_from_env(os.environ)
        catalog = os.environ.get("FILMIQ_REVIEWED_CATALOG")
        catalog_path = Path(catalog) if catalog and Path(catalog).is_absolute() else None
        if catalog_path:
            from reviewed_catalog import catalog_facts

            def read_reviewed(ident, title):
                return catalog_facts(catalog_path, ident, title)
        else:
            read_reviewed = None

        def load():
            return decode_allowlist(ALLOWLIST_PATH.read_text(encoding="utf-8"))

        parse_allowlist(load())
        cache = None
        if os.environ.get("FILMIQ_TMDB_CACHE_ENABLE", "0") != "0":
            from tmdb_live_cache import from_env

            cache = from_env(os.environ)
    except (OSError, ValueError, TypeError):
        raise SystemExit("Live bridge configuration unavailable") from None
    with make_server(
        "127.0.0.1",
        15178,
        app(config, load, read_movie, read_reviewed, cache),
        handler_class=QuietHandler,
    ) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
