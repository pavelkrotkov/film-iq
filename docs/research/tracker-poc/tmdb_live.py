"""Optional loopback TMDB read-through; stores no responses or credentials.

This service only returns public movie metadata, not personal film data. It is
an experiment, not a rights certification. Supply the existing TMDB credential
in the process environment and stop the service when testing is finished.
"""

import json
from urllib.parse import urlparse

from tmdb_readonly import TMDbError, read_movie
from waitress import serve

ALLOWED_ORIGINS = {"http://localhost:15174", "http://localhost:18180"}


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
    start(status, headers)
    return [body]


def safe_provider_link(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.hostname == "www.themoviedb.org":
        return value
    return None


def app(reader=read_movie):
    def application(environ: dict, start):
        origin = environ.get("HTTP_ORIGIN", "")
        if origin and origin not in ALLOWED_ORIGINS:
            return response(start, "403 Forbidden", {"error": "Origin not allowed"}, origin)
        path = environ.get("PATH_INFO", "").split("/")
        if (
            environ.get("REQUEST_METHOD") != "GET"
            or len(path) != 3
            or path[1] != "movie"
            or not path[2].isascii()
            or not path[2].isdigit()
            or not 0 < int(path[2]) <= 2_147_483_647
        ):
            return response(start, "404 Not Found", {"error": "Not found"}, origin)
        try:
            movie = reader(int(path[2]))
        except (TMDbError, ValueError, OSError):
            return response(start, "502 Bad Gateway", {"error": "TMDB unavailable"}, origin)
        observation = movie.availability
        link = next(
            (url for offer in observation.offers if (url := safe_provider_link(offer.url))), None
        )
        payload = {
            "tmdb_id": movie.tmdb_id,
            "title": movie.title,
            "synopsis": movie.synopsis,
            "year": movie.year,
            "genres": movie.genres,
            "directors": movie.directors,
            "poster_url": movie.poster_url,
            "availability": {
                "status": observation.status,
                "checked_at": observation.checked_at.isoformat(),
                "provider_url": link,
                "offers": [{"provider": o.provider, "kind": o.kind} for o in observation.offers],
            },
        }
        return response(start, "200 OK", payload, origin)

    return application


if __name__ == "__main__":
    serve(app(), host="127.0.0.1", port=15176)
