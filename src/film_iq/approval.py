"""Preview a single recommendation before authorizing a future sync."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Preview:
    title: str
    tmdb_id: int

    def __post_init__(self) -> None:
        if not self.title.strip() or type(self.tmdb_id) is not int or self.tmdb_id <= 0:
            raise ValueError("a title and positive TMDB movie ID are required")


def approved_movie(preview: Preview, *, approved: bool = False) -> int:
    """Return the previewed TMDB ID only after an explicit approval."""
    if approved is not True:
        raise PermissionError("explicit approval of the preview is required")
    return preview.tmdb_id


class WriteBackend(Protocol):
    """Adapter must use complete authoritative reads and propagate failures."""

    def find_movie(self, tmdb_id: int) -> int | None: ...
    def on_watchlist(self, movie_id: int) -> bool: ...
    def add_movie(self, tmdb_id: int, *, approved: bool = False) -> int: ...
    def add_watchlist(self, movie_id: int, *, approved: bool = False) -> None: ...


def sync_one(
    preview: Preview, backend: WriteBackend, *, execute: bool = False, approved: bool = False
) -> str:
    """Preview by default; approved execution re-reads state before each addition.

    Retry after an uncertain write only after the adapter can reliably read its result.
    This is a seam for a verified adapter, not an HTTP client.
    """
    if not execute:
        return f"Preview: add {preview.title} (TMDB {preview.tmdb_id}) to watchlist"
    tmdb_id = approved_movie(preview, approved=approved)
    movie_id = backend.find_movie(tmdb_id)
    if movie_id is None:
        movie_id = backend.add_movie(tmdb_id, approved=True)
    if backend.on_watchlist(movie_id):
        return "already on watchlist"
    backend.add_watchlist(movie_id, approved=True)
    return "added to watchlist"
