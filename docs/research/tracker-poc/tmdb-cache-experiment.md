# Fictional TMDb cache experiment

This experiment is **not enabled for real provider data** and is not connected
to either running film interface. It uses a separate project-local directory,
not tracker history or a new database. No provider credentials or live requests
are used by the checks below.

The draft stores film metadata and provider observations as separately expiring
sections. A later partial or failed provider response does not replace a complete
observation; an incomplete metadata refresh is reported rather than silently
extending the older section. A separate authority file records policy decisions
and per-film purge marks. A cache restored with the latest independent authority
cannot extend an older deadline; simultaneous rollback or loss of both remains
unsupported. Corrupt records are reported for review when their expiry cannot
be established, while independently expired records can still be purged.

The current checks use only fictional records and explicit fictional permission:

```sh
PYTHONPATH=docs/research/tracker-poc uv run --no-sync python docs/research/tracker-poc/tmdb_cache_check.py
PYTHONPATH=docs/research/tracker-poc uv run --no-sync python docs/research/tracker-poc/tmdb_cache_recovery_check.py
PYTHONPATH=docs/research/tracker-poc uv run --no-sync python docs/research/tracker-poc/cache_vertical_check.py
```

The offline vertical check runs the two existing adapter classes with mocked
tracker transports. A separate `cache_vertical_live_check.py` can use a
dedicated fictional Kaneo fixture directory and YouTrack `FILMPOC`; each run
creates and leaves one fictional record in each tracker. It was run against
the local trackers: repeat import, user edits, partial and failed refreshes,
fresh-process cache read and test-only UI filter projections passed. The cache
projection is not a deployed bridge or browser verification.

Real activation still requires a reviewed TMDb-specific use and retention
policy, an inventory and purge procedure for all actual copies, an expiry
mechanism when services are stopped, and a recovery procedure that preserves
the latest authority independently. The existing source terms and project
decisions are described in [the intended-use assessment](../availability/intended-use-20261031.md)
and [recovery policy](../../operations-recovery.md). Do not infer permission
from an API key or from these synthetic checks.
