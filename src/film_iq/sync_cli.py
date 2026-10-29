"""CLI seam for previewing or explicitly executing one watchlist addition."""

import os

from film_iq.approval import Preview, approved_movie, sync_one
from film_iq.movary_http import MovaryHTTPTransport
from film_iq.movary_write import MovaryWriteBackend


def sync_watchlist(
    title: str, tmdb_id: int, *, execute: bool = False, approved: bool = False
) -> str:
    """Preview without config/I/O; execution requires literal approved=True."""
    preview = Preview(title, tmdb_id)
    if not execute:
        return f"Preview: add {preview.title} (TMDB {preview.tmdb_id}) to watchlist"
    approved_movie(preview, approved=approved)
    base_url, username, token = (
        _required_env(name) for name in ("MOVARY_URL", "MOVARY_USERNAME", "MOVARY_TOKEN")
    )
    backend = MovaryWriteBackend(preview, username, MovaryHTTPTransport(base_url, token))
    return sync_one(preview, backend, execute=True, approved=approved)


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise ValueError(f"{name} is required for Movary execution")
    return value
