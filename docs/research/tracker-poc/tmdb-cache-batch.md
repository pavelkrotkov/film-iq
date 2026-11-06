# Opt-in local cache batch candidate

The runner populated the 130 already authorized records in each local POC
on November 5–6, 2026. A cache-only comparison found 130 valid entries in both,
with matching metadata and availability status; the 109 comparable provider
sets matched and 21 observations were unknown in both. This checks local cache
responses, not personal entitlement or independently verified film identity.
The runner does not change bridge configuration.

For a permitted batch, each invocation processes exactly one backend:

```sh
cd /Users/pavel/dev/film-iq/.worktrees/kaneo-youtrack
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc/youtrack-tmdb-live-bridge:docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_cache_batch.py --backend kaneo --run
```

Use `--backend youtrack` for a separate invocation. Run the backends
sequentially, with no other live refreshes using the same credential: the
transport limiter is per bridge process, not shared across them. **Before**
running, deploy the reviewed transport changes and start the idle bridge with
`FILMIQ_TMDB_REFRESH_ENABLED=0`. Then start the active bridge with
`FILMIQ_TMDB_PACE=1` and `FILMIQ_TMDB_REFRESH_ENABLED=1`, configure its
authorized provider allowlist and cache, and ensure the YouTrack issue handler
with its cache endpoints is installed. Only one bridge may refresh during a
bounded batch; the paused bridge still serves cache and catalog reads. Pause
the active bridge before enabling the other for a later pass. These local
controls do not coordinate other clients using the same provider credential.
After the automated run, both interfaces can be enabled for interactive use;
their independent limiters do not enforce a shared aggregate request rate.
The UI can request more than 25 films, so its bulk controls do not inherit the
runner's 25-film/75-attempt limit.
The runner reads each bridge's effective settings through its authenticated
local status endpoint and stops with `pacing_not_established` if it cannot
establish that the required pacing and pause settings are active. For YouTrack
status, it uses the already selected
pilot issue and verifies its identity and visibility first. Neither status
endpoint contacts TMDb or exposes credentials.

The runner verifies the 130-ID approval against the exact private source
manifest and the recorded hashes of that manifest and watched-approval preview,
then validates a unique, visible record for every approved ID. It reads the
selected backend's cache and skips
fresh entries, then requests at most 25 uncached films. Each successful refresh
must be followed by a matching, unexpired cache-only read. Only an explicit
cache-miss response permits refresh: rate limits, authentication or approval
failures, ambiguous responses and all other errors stop immediately, without
retry. The report contains aggregate counts and a generic outcome. A failed
readback can follow an already successful refresh; `attempted` records the
request even when `refreshed` is not incremented. The runner makes no tracker
field or Movary writes and does not create another database. A film refresh can
perform multiple provider requests, and JSON cache reads do not fetch images.
Keep the approved-ID file and source evidence unchanged for the duration of
each invocation; the runner validates them at the start, not continuously.
The aggregate report separately counts complete, partial and unknown provider
observations; a successful metadata refresh does not imply complete streaming
availability, and unknown is not treated as absent.

The read-only comparison can be repeated after both bridges are running. It
reads the approved tracker mappings and cache-only endpoints; it makes no
provider requests and prints aggregate counts only:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc/youtrack-tmdb-live-bridge:docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_cache_compare.py
```

Fictional checks (no real tracker or provider requests):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc/youtrack-tmdb-live-bridge:docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_cache_batch_check.py
```
