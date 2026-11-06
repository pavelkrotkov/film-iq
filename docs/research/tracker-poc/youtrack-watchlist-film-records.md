# Neutral records for the two observed watchlist films

On November 6, 2026, the local YouTrack `FILMREAL` POC had two entries in the
current user's imported Movary watchlist property without corresponding visible
canonical issues. A private, owner-only preview identified two pending records,
zero existing records, and zero conflicts. After independent review, a single
guarded run created two neutral film issues. It supplied the observed title and
TMDb ID, the `Discovery` lifecycle value, and general provenance. The IDs and
titles are source assertions, not independently verified film matches. The issue
payload contained no watchlist status, watched status, ratings, or personal notes.

The run verified each created issue's submitted title, ID, lifecycle, provenance,
and empty description. Its before-and-after comparison found the original 130
issue projections, the current user's full watched and watchlist property
exports, visible preferences, and provider-approval file bytes unchanged. The
preferences comparison used the available visible projection, not a full raw
property export. No Movary or personal-list update, provider request, or retry
occurred. A later read-only preview returned **zero pending, two existing, and
zero conflicts**. Both original and post-import previews remain in the ignored,
owner-only project cache and contain private titles and IDs; do not commit them.

The import affects YouTrack only. The two entries remain unmatched to canonical
Kaneo records; no Kaneo credentials or browser sessions were used. The two IDs
remain outside the existing provider allowlist. Matching and rendering the new
YouTrack records in the film UI have not been verified by this import.

## Guarded tool

[`youtrack_watchlist_films.py`](youtrack_watchlist_films.py) reads the supplied
complete local Movary observation, the current user's watchlist export and
view, the existing provider approval, and the complete visible `FILMREAL`
issue listing. It requires exactly two observed entries and refuses duplicate
IDs, mismatched or colliding normalized titles, provider-allowlisted pending
IDs, or an unexpected project. It writes a new owner-only preview without
changing tracker records. On apply it compares the preview with current data,
rechecks the source, property, approval, project and remaining identities before
each creation, and stops without retry if a creation's result is uncertain. It
does not call enrichment or modify existing issues. Use a single writer:
YouTrack does not enforce uniqueness of this custom TMDb ID field.

For a read-only preview, from the worktree root provide a complete, private
snapshot and a **new** path inside `.cache/tracker-poc/private`:

```sh
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python \
  docs/research/tracker-poc/youtrack_watchlist_films.py \
  --snapshot .cache/tracker-poc/private/PATH-TO-SNAPSHOT.json \
  --preview .cache/tracker-poc/private/NEW-PREVIEW.json
```

Applying a preview creates real tracker issues and should be coordinated with
the actual POC owner and checked against current configuration. The tool is a
bounded experiment for these two observed entries, not a general Movary sync.
The fictional workflow checks run with:

```sh
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python \
  docs/research/tracker-poc/youtrack_watchlist_films_check.py
```
