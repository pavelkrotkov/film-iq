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

### YouTrack-only on-demand mode without a Kaneo session

The `--kaneo-offline` option is a fictional-test-verified alternative for
`--backend youtrack`. It constructs only the YouTrack API-token client and
does not load the Kaneo cookie jar. The runner requires no listener on the
local Kaneo bridge port before starting and checks again before each provider
refresh; an occupied port or failed listener inspection stops the run. It
still verifies the approved collection, issue identities, and the YouTrack
bridge's enabled, paced settings. Do not start the Kaneo bridge or another
client using the same provider credential during the run: local preflight and
per-film checks do not provide an atomic cross-process rate limiter.

For an explicitly chosen on-demand run, stop only the recorded Kaneo pilot
using its `--stop` command, then run the batch with `--backend youtrack
--kaneo-offline --run`; use `--refresh-window 0` through `5` only when an
existing cache entry should be refreshed. Kaneo's cache and catalog reads are
unavailable while its bridge is stopped. Afterward, restart it with the
documented [recorded-configuration startup](local-runbook.md#kaneo-collection-cache).
The mode has not been exercised against the real trackers or provider, and it
does not install or authorize a schedule.

## Optional periodic refresh windows

The default runner only fills cache misses. To refresh an existing observation
on a chosen cadence, supply `--refresh-window` as well as `--run`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc/youtrack-tmdb-live-bridge:docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_cache_batch.py --backend kaneo --run --refresh-window 0
```

Windows `0` through `5` partition the approved 130 IDs in a deterministic
order. Each of the first five covers 25 films; the last covers five. A window
refreshes its films even when their cache entries are still fresh. It verifies
each cache readback and stops at the first error; `complete` refers to that
window only. A deliberate retry can re-fetch earlier successful films in the
window, but does not create tracker records or alter personal preferences.
Unknown availability remains unknown; the window does not infer that a
provider is absent or treat a metadata timestamp as a successful provider
check.

These are manually invoked one-shots; no schedule is installed. The windows
include the watched-history IDs, whose existing provider-request authorization
covers on-demand refreshes, not unattended scheduled requests. Do not schedule
these windows under the current authorization. A discovery-only subset from
an old snapshot cannot guarantee that a film has not since been watched.

The command does not switch bridges, renew a source policy, or manage other
clients. An operator must keep the other bridge refresh-paused and the selected
bridge paced and enabled for each invocation, as above. If both bridges are
enabled, the command fails its preflight without contacting TMDb. The scope is
the authorized collection, not a watchlist-only selection. The existing
30-day policy window, cache expiry and stopped-host limitations still apply.

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
