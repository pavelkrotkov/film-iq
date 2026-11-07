# Kaneo fictional lifecycle round trip

On November 6, 2026, the isolated Kaneo 2.49.0 API-key fixture ran the real
synthetic enrichment worker against a new fictional film. Its source and US
subscription, rental and purchase providers were fictional and made no network
requests. The worker's backend was configured with a newly issued fictional
bearer key; its normal cookie-based CLI was not used for this check.

The fixture renamed three fictional board columns to Discovery, Evaluation and
Watchlist, then moved the film through those states, Archived and back to
Evaluation. After each of the five transitions, it read the task and board and
compared the title, synopsis, every returned custom-field value and complete
stored provider observation. The archived and active board buckets also matched
each state. All checks passed. No real POC data, browser session, Movary record
or external provider was accessed.

Repeat with the pinned images already present locally:

```sh
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python \
  docs/research/tracker-poc/kaneo_bearer_live_fixture.py
```

Each invocation creates separate internal-only containers and a project-local
fictional data directory. The containers stop on completion and the fixture data
is retained. This test does not establish real-film browser behavior, metadata
outside the checked fields, concurrent-writer safety or live POC recovery.
