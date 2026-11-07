"""Serialize the shared read-through response without storing provider data."""

from urllib.parse import urlparse

from tmdb_readonly import Movie


def safe_provider_link(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.hostname == "www.themoviedb.org":
        return value
    return None


def movie_payload(movie: Movie) -> dict:
    observation = movie.availability
    link = next(
        (url for offer in observation.offers if (url := safe_provider_link(offer.url))), None
    )
    return {
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "original_title": movie.original_title,
        "synopsis": movie.synopsis,
        "year": movie.year,
        "genres": movie.genres,
        "directors": movie.directors,
        "poster_url": movie.poster_url,
        "imdb_title_url": movie.imdb_title_url,
        "availability": {
            "status": observation.status,
            "checked_at": observation.checked_at.isoformat(),
            "provider_url": link,
            "offers": [{"provider": o.provider, "kind": o.kind} for o in observation.offers],
        },
    }
