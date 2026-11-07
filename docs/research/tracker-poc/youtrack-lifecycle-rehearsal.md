# YouTrack fictional lifecycle round trip

On November 6, 2026, the local YouTrack Server 2026.2.19728 POC created one
new fictional issue in `FILMPOC` using its API integration credential. A
fixture-only worker attached fictional metadata and separate subscription,
rental and purchase provider values. The issue then moved through Discovery,
Evaluation, Watchlist, Archived and back to Evaluation.

After every transition, the test read back the entire requested issue
projection except the intentionally changed lifecycle field, and compared the
complete stored provider observation. All five transitions and comparisons
passed. The fixture issue remains in `FILMPOC` for inspection. No real film,
Movary record, browser session or external provider was accessed. The test does
not establish browser behavior, other fields outside the requested projection,
concurrent-writer safety or production recovery.

To repeat against the configured local POC, with a single fixture writer:

```sh
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python \
  docs/research/tracker-poc/youtrack_lifecycle_live_check.py
```

Every successful or partially successful invocation can leave a new fictional
issue. The script stops on its first failure and does not retry an unconfirmed
mutation; inspect the fixture project before retrying.
