"""Opt-in, uncached MDBList lookup for the local Kaneo POC.

The upstream key stays server-side. The loopback endpoint requires the local
Kaneo session and only accepts the POC UI origin. No tracker writes occur.
"""

import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

from preferences import current_user

from film_iq.availability.candidate_transport import _NoRedirect

ORIGIN = "http://localhost:15174"
KEY_FILE = Path(".cache/tracker-poc/private/mdblist-key")
SOURCE_TYPES = {
    "tomatoes": ("Rotten Tomatoes", "critic", "rottentomatoes.com"),
    "popcorn": ("Rotten Tomatoes", "audience", "rottentomatoes.com"),
    "tomatoesaudience": ("Rotten Tomatoes", "audience", "rottentomatoes.com"),
    "metacritic": ("Metacritic", "critic", "metacritic.com"),
    "metacriticuser": ("Metacritic", "audience", "metacritic.com"),
    "rogerebert": ("Roger Ebert", "critic", "rogerebert.com"),
    "imdb": ("IMDb", "audience", "imdb.com"),
    "tmdb": ("TMDB", "audience", "themoviedb.org"),
    "trakt": ("Trakt", "audience", "trakt.tv"),
    "letterboxd": ("Letterboxd", "audience", "letterboxd.com"),
    "myanimelist": ("MyAnimeList", "audience", "myanimelist.net"),
}


class MDBListError(Exception):
    pass


def _safe_url(value, domain):
    if not isinstance(value, str):
        return None
    try:
        parsed = urllib.parse.urlsplit(value)
        host = parsed.hostname or ""
        if (
            parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
            or not (host == domain or host.endswith("." + domain))
        ):
            return None
    except ValueError:
        return None
    return value


def _number(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def normalize(payload, tmdb_id):
    """Reject missing/mismatched identity; never infer unavailable ratings or URLs."""
    if type(tmdb_id) is not int or tmdb_id <= 0:
        raise ValueError("TMDB ID must be a positive integer")
    if not isinstance(payload, dict):
        raise MDBListError("MDBList response was invalid")
    ids = [payload[key] for key in ("tmdbid", "tmdb_id") if key in payload]
    if not ids or any(type(value) is not int or value != tmdb_id for value in ids):
        raise MDBListError("MDBList response identity did not match")
    rows = payload.get("ratings")
    if not isinstance(rows, list):
        raise MDBListError("MDBList ratings were unavailable")
    ratings = []
    for row in rows:
        if not isinstance(row, dict):
            raise MDBListError("MDBList ratings were malformed")
        source = row.get("source")
        if not isinstance(source, str) or not re.fullmatch(r"[a-z0-9_]{1,40}", source):
            raise MDBListError("MDBList ratings were malformed")
        label, kind, domain = SOURCE_TYPES.get(source, (source, "unknown", ""))
        value, score, votes = _number(row.get("value")), _number(row.get("score")), row.get("votes")
        if score is not None and not 0 <= score <= 100:
            score = None
        if type(votes) is not int or votes < 0:
            votes = None
        ratings.append(
            {
                "source": source,
                "source_name": label,
                "kind": kind,
                "value": value,
                "score_100": score,
                "votes": votes,
                "url": _safe_url(row.get("url"), domain) if domain else None,
                "via": "MDBList",
            }
        )
    return {"tmdb_id": tmdb_id, "ratings": ratings, "source": "MDBList"}


def fetch_movie(tmdb_id, key_file=KEY_FILE, opener=None):
    if type(tmdb_id) is not int or tmdb_id <= 0:
        raise ValueError("TMDB ID must be a positive integer")
    try:
        key = key_file.read_text().strip()
        if not key or "\n" in key or "\r" in key:
            raise ValueError
    except (OSError, ValueError):
        raise MDBListError("MDBList key unavailable") from None
    query = urllib.parse.urlencode({"apikey": key})
    request = urllib.request.Request(
        f"https://api.mdblist.com/tmdb/movie/{tmdb_id}/?{query}",
        headers={"Accept": "application/json"},
    )
    try:
        with (opener or urllib.request.build_opener(_NoRedirect)).open(
            request, timeout=20
        ) as response:
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise MDBListError("MDBList response was too large")
        payload = json.loads(raw)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise MDBListError("MDBList rate limit reached; retry later") from None
        raise MDBListError(f"MDBList returned HTTP {error.code}") from None
    except (urllib.error.URLError, OSError, ValueError, UnicodeError):
        raise MDBListError("MDBList request or response failed") from None
    return normalize(payload, tmdb_id)


def _response(start, status, payload):
    body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
    start(
        status,
        [
            ("Content-Type", "application/json"),
            ("Cache-Control", "no-store"),
            ("Access-Control-Allow-Origin", ORIGIN),
            ("Access-Control-Allow-Credentials", "true"),
            ("Vary", "Origin"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def application(environ, start):
    if environ.get("HTTP_ORIGIN") != ORIGIN:
        return _response(start, "403 Forbidden", {"error": "Origin not allowed"})
    if environ.get("REQUEST_METHOD") != "GET":
        return _response(start, "405 Method Not Allowed", {"error": "Method not allowed"})
    match = re.fullmatch(r"/ratings/([1-9][0-9]{0,9})", environ.get("PATH_INFO", ""))
    if not match:
        return _response(start, "404 Not Found", {"error": "Not found"})
    try:
        current_user(environ)
    except Exception:
        return _response(start, "401 Unauthorized", {"error": "Kaneo session required"})
    try:
        result = fetch_movie(int(match.group(1)))
    except MDBListError as error:
        return _response(start, "502 Bad Gateway", {"error": str(error)})
    except Exception:
        return _response(start, "502 Bad Gateway", {"error": "MDBList lookup unavailable"})
    return _response(start, "200 OK", result)


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    with make_server("127.0.0.1", 15177, application, handler_class=QuietHandler) as server:
        server.serve_forever()
