# Local tracker POC runbook

This is for the **existing configured Mac installation**, not a new setup or a
Hermes deployment. Start Docker Desktop first. In each terminal begin at the
same worktree root:

```sh
cd /Users/pavel/dev/film-iq/.worktrees/kaneo-youtrack
```

The original setup, pinned images, YouTrack app installation and credentials
are described in [the POC README](README.md). The commands below start the
existing named containers and do not create or replace them. If a named container,
project-local configuration, interpreter or built UI is missing, stop and use
the documented initial setup; do not run the bootstrap or seed commands against
this existing installation. Keep the ignored `.cache/tracker-poc/` directory,
including credentials, private inputs and both tracker databases, private.

## One-command manual startup

With Docker Desktop running, start the existing configured POCs from the
worktree root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/start_local_pocs.py
```

The command checks the existing containers, built UI, preference database and
recorded collection pilot settings before starting anything. It reads the
preference database schema without reading preference rows or initializing a
missing table; a database whose schema is unavailable in the main file is
rejected. It starts only
stopped named containers, waits for PostgreSQL and the tracker web endpoints,
and checks that the YouTrack metadata bridge responds to an unauthenticated
loopback request inside its container. This checks responsiveness, not that an
authenticated metadata request will succeed. It starts the separate UI,
preference bridge and Kaneo metadata bridge only when their ports are free. It
preserves the recorded pilot scope, pacing and
refresh setting. The UI and preference bridge run in the background with
owner-only logs in `.cache/tracker-poc/private/`; the pilot uses its existing
private log. The pilot's normal startup performs its configured expired-cache
cleanup. No metadata provider lookup is made by this command.

An occupied port is left untouched and reported as **not verified**; the
command exits with status 2 in that case. A missing prerequisite, unavailable
Docker service or failed readiness check stops the command with status 1;
services already started during that run remain running. Inspect the message
and the commands below before retrying. HTTP reachability does not verify a
signed-in session or the full film workflow. On 2026-11-06, a run against the
already-running installation found all four named containers running and left
the occupied UI, preference and Kaneo metadata listeners untouched and marked
unverified. It exited with status 2 and made no provider requests. This did
not test starting stopped services. A separate isolated rehearsal exercised
the actual startup orchestrator with fake Docker state and three real fictional
loopback processes, including a repeat run and recovery after stopping the
fictional preference process. It did not start real trackers, use provider
credentials or test a real cross-service restart. Run it from the worktree root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/start_local_pocs_rehearsal.py
```

Real cold startup remains untested. This is manual startup, not an automatic
reboot service.

## Tracker containers

Start the existing PostgreSQL first and check that it reports `accepting
connections`. If it is still starting, repeat the readiness command before
starting Kaneo. Start YouTrack before its metadata bridge:

```sh
docker start film-iq-tracker-poc-postgres-1
docker exec film-iq-tracker-poc-postgres-1 pg_isready -U kaneo -d kaneo
docker start film-iq-tracker-poc-kaneo-1
docker start film-iq-tracker-poc-youtrack-1
docker start film-iq-tracker-poc-tmdb-live-bridge-1
```

These processes stay in Docker; this terminal can be closed. YouTrack can take
some time to become responsive. Sign in to Kaneo at
[localhost:15173](http://localhost:15173/auth/sign-in), using the generated POC
account in the owner-only `.cache/tracker-poc/kaneo-test-user.json`, then open
the film UI at [localhost:15174](http://localhost:15174/) and select **FilmIQ
Private Input POC / Private Film Records**. Sign in to
[YouTrack](http://localhost:18180/) with the existing administrator account and open **FilmIQ POC** from the main menu. The installed YouTrack app
runs inside YouTrack; it does not use the separate Kaneo UI server.

YouTrack's configured backups are under `.cache/tracker-poc/youtrack/backups`.
One manual backup was created and checked on 2026-11-05; it is owner-only and
contains private data. A newly created archive was initially readable by other
local users, so check and restrict permissions for each future backup. Automatic
backups are disabled. The existing local archive has not been restored and is
not a separate-machine copy. See [JetBrains' backup instructions](https://www.jetbrains.com/help/youtrack/server/back-up-the-database.html).

The current YouTrack `FILMREAL` watched snapshot is v3: it contains 27 current
entries from a newer complete Movary observation and separately preserves the
11 unbound histories from the earlier mixed-v2 snapshot, with their original
observation time. The prior v2 migration had 16 inferred bindings and 11
unbound entries; neither those inferences nor the current supplied IDs
independently verify film identity. Unbound historical evidence does not by
itself mark the current film watched.

Owner-only full current-user watched-property exports were saved before and
after the v3 refresh; the post-refresh property matched the expected state.
Earlier v1 project projections were visibility-filtered and were not full
property backups. The full-property restore passed an isolated fictional test;
real-data restoration and full server recovery remain unverified. See the
[watched-property backup and recovery notes](watched-property-backup.md) before
changing or downgrading the FilmIQ app.

Restart Kaneo alone with `docker restart film-iq-tracker-poc-kaneo-1`. For a
PostgreSQL restart, stop Kaneo first, restart PostgreSQL, repeat the `pg_isready`
check above until it succeeds, then start Kaneo:

```sh
docker stop film-iq-tracker-poc-kaneo-1
docker restart film-iq-tracker-poc-postgres-1
docker exec film-iq-tracker-poc-postgres-1 pg_isready -U kaneo -d kaneo
docker start film-iq-tracker-poc-kaneo-1
```

For a YouTrack restart, stop its namespace-sharing metadata bridge first and
start it again after YouTrack is running:

```sh
docker stop film-iq-tracker-poc-tmdb-live-bridge-1
docker restart film-iq-tracker-poc-youtrack-1
docker start film-iq-tracker-poc-tmdb-live-bridge-1
```

`docker restart` alone does not reload changed container environment or mounts.
The bridge relies on the existing YouTrack container and its configuration;
recreating either container requires the separate setup instructions, not these
restart commands. Restarting services interrupts active requests.

## Kaneo UI and preference bridge

These are separate foreground processes. Use **one terminal for each** and leave
it open. If a port is already occupied, do not launch another copy; check the
listeners using the status command below.

Terminal A, UI:

```sh
cd /Users/pavel/dev/film-iq/.worktrees/kaneo-youtrack/docs/research/tracker-poc/ui
python3 -m http.server 15174 --bind 127.0.0.1
```

Terminal B, preference and read-only watched-snapshot bridge:

```sh
cd /Users/pavel/dev/film-iq/.worktrees/kaneo-youtrack
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/preferences.py
```

To stop either process, press **Ctrl-C in its own terminal**. To restart it,
press Ctrl-C, wait for it to exit, and run its command again. The preference
bridge uses the existing project-local SQLite file and separately scoped
read-only watched snapshot. Restarting it invalidates pending preview tokens;
start a new preview if needed. It does not change Movary.

## Movary watchlist projection

On 2026-11-06, the Kaneo bridge and UI were updated to display positive
Movary watchlist observations separately from editable POC preferences. The
complete source snapshot yielded two entries, and neither ID was in the
original film-import manifest. No tracker records were created during this
rollout; creating an unmatched entry requires an explicit user submission.
Current live tracker matching and authenticated UI rendering have not been
independently verified. The UI
preserves the source observation time, displays source titles and IDs as
unverified, and treats missing observations as unknown. Showing the entries
does not query TMDb or another provider; no real Movary watchlist or provider
writes were made.

The one-time initializer matched the existing single watched-sidecar owner and
project to the same complete source observation, previewed two entries, and
created a separate owner-only `movary-watchlist.json` without altering the
watched sidecar. Matching the observation supports continuity but does not
independently verify the user's identity. The initializer refuses an existing
target and assumes a single writer. For later observations use the manual
refresh below rather than removing or overwriting the sidecar to force a refresh.

For a future manual refresh, first refresh the existing watched sidecar to the
same complete Movary snapshot using its separately documented procedure. Stop
any other sidecar writers. Matching observations establish continuity, not
independent account identity. Then preview the watchlist projection using an
owner-only project-local snapshot and status file:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/kaneo_watchlist_refresh.py --snapshot <project-private-snapshot.json>
```

Review the observation times and aggregate additions and no-longer-observed
counts. The latter are not off-watchlist assertions. For a confirmed refresh,
run the same command with `--apply --backup <new-owner-only-project-backup>`;
the backup path must be unused inside an owner-only project directory. The
helper requires exactly one existing watched-sidecar owner and a matching project
and complete source, accepts a newer observation, copies and verifies the exact
old bytes, rechecks inputs, and changes only that owner's watchlist projection.
Other watchlist-sidecar users are preserved. A same observation is a no-op; older
or conflicting same-time data is rejected. It assumes a single writer. It
contacts neither Movary, the tracker, nor any provider. No real refresh has
been exercised by this helper.

Recovery is manual, not an automatic guarded restore: stop concurrent sidecar
writers; verify the owner-only backup and current sidecar belong to the same
owner and project; first save the entire current sidecar to a separate unused
owner-only project file, then restore the exact selected backup and verify
readback byte for byte before restarting writers. If any ownership or integrity
check is unclear, stop and investigate. Do not restore merely because an apply
reported an error: inspect the current sidecar and retained backup first.

A private SQLite online backup passed integrity verification. After restart,
the preferences database's complete SQL-dump digest matched the backup; source
and watched-sidecar hashes and the new sidecar readback were unchanged. The
bridge returned 403 to an anonymous watchlist request. The first restart
attempt resolved the `.venv/bin/python` symlink and thus bypassed the virtual
environment; it exited before binding because the project package was missing.
Launching the exact `.venv/bin/python` path restored the service. Restarting
invalidates pending preference preview tokens, so those must be previewed again.

The new UI asset was checked against the bytes served by the local web server.
The exact previous bundle and database backup are retained under
`.cache/tracker-poc/private/kaneo-watchlist-rollout-laaym4pe/`; the bridge log
there records the initial failed launch. These delivery and denial checks do not
establish authenticated real-film browser behavior or full recovery.

## Approved-ID TMDB bridges

The YouTrack bridge is the Docker container started above. Its existing
container stores its configuration and shares YouTrack's network namespace; it
publishes no separate host port. To restart it alone, run:

```sh
docker restart film-iq-tracker-poc-tmdb-live-bridge-1
```

### YouTrack collection cache

The existing bridge container now runs the 130-film cache POC. The restart
command above preserves its current mounts and environment. It does not apply
changes to the Compose files. The pilot keeps the original approved collection
for local catalog reads and provider refreshes.
Its separate private cache is under
`.cache/tracker-poc/private/tmdb-live-cache/youtrack/`. Check the container's
state and its logs for the generic `TMDB cache maintenance failed` message;
absence of the message is not a worker heartbeat. Hourly cleanup stops when
the bridge or host stops. The seven-day display limit is not a guarantee of
physical deletion while stopped.

If the existing bridge must be **recreated**, retain all four overrides so its
reviewed catalog and separate approval scopes remain available. From the
worktree root, with Docker Desktop and YouTrack running:

```sh
export FILMIQ_APPROVAL_DIR="$PWD/.cache/tracker-poc/private/tmdb-approval"
export FILMIQ_CATALOG_APPROVAL_HOST_DIR="$PWD/.cache/tracker-poc/private/tmdb-approval"
export FILMIQ_YOUTRACK_CACHE_DIR="$PWD/.cache/tracker-poc/private/tmdb-live-cache/youtrack"
export FILMIQ_BRIDGE_UID="$(id -u)" FILMIQ_BRIDGE_GID="$(id -g)"
export FILMIQ_TMDB_BRIDGE_ENABLE_LIVE=1 FILMIQ_TMDB_PACE=1 FILMIQ_TMDB_REFRESH_ENABLED=1
export FILMIQ_REVIEWED_CATALOG_FILE="$PWD/../../.cache/epic-c/results/reviewed-display-catalog-expanded-20261031.json"
docker compose -f docs/research/tracker-poc/compose.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.live.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.catalog.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.cache.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.catalog-approval.yaml \
  --profile tmdb-live-bridge up -d --no-deps --force-recreate --pull never tmdb-live-bridge
```

The credential remains in the existing private Compose env file. The saved
pre-pilot app packages are under
`.cache/tracker-poc/private/youtrack-pilot-rollback-i792iwgg/`. An older FilmIQ
handler cannot read v3 watched data. The current v3 snapshot contains historical
entries, so `restore-legacy` refuses to discard that history; do not downgrade
the handler. Review the [full-property recovery notes](watched-property-backup.md)
and the compatibility of every project before any future rollback. Property
restoration has been tested on fictional data, not the real snapshot. Update
existing apps in place; deleting an app deletes its app-owned data. Recreating the original bridge also requires the original
full approval directory and live plus catalog overrides without the two
pilot overrides. See the [cache candidate notes](tmdb-live-cache-candidate.md)
for the stopped-writer purge procedure and retention limits.

### Kaneo collection cache

The active POC uses the 130-film approved collection, a seven-day observation
limit and a fixed policy window in the separate private Kaneo cache.
Its bridge runs in the background. To start the pilot after a reboot or restart
its currently running bridge without changing either tracker, its UI, or Movary:

```sh
cd /Users/pavel/dev/film-iq/.worktrees/kaneo-youtrack
FILMIQ_TMDB_PACE=1 FILMIQ_TMDB_REFRESH_ENABLED=1 .venv/bin/python docs/research/tracker-poc/kaneo_live_pilot.py --collection
```

If the port is free, the command starts the pilot even when its PID record is
missing or stale. If the port is occupied, it verifies that the recorded pilot
PID owns the listener before stopping it; an unrecognized listener is left
untouched. It then starts the same pilot configuration. It reads the
provider credential from the existing private env file and passes it only in
the process environment. Standard output and errors go to the owner-only
`.cache/tracker-poc/private/kaneo-live-pilot.log`; inspect this log for
`TMDB cache maintenance failed`. This is a manual check, not an alert. The PID
record is `.cache/tracker-poc/private/kaneo-live-pilot-pid.json`. If an existing
listener does not match, investigate it before proceeding.
An hourly cleanup only runs while the bridge is running; host-off deletion
still requires an operator. Cache-only reads do not call TMDb. The original UI
bundle is saved at `.cache/tracker-poc/kaneo-live-pilot-original.js` for rollback.
To stop only this recorded bridge, run
`.venv/bin/python docs/research/tracker-poc/kaneo_live_pilot.py --stop`; it
leaves an unrecognized listener untouched. For an offline policy renewal, stop
both writers and follow the [renewal procedure](tmdb-live-cache-candidate.md#renewing-the-policy-window).

### Ordinary Kaneo bridge without the cache pilot

The non-pilot Kaneo bridge is a **third foreground terminal**. Do not run this
ordinary launcher while the pilot is active; it does not enable the pilot cache
or its separate catalog scope. The command below reads
only the TMDB credential from the existing project-local YouTrack bridge env
file as data. It does not source or execute the file, print the credential, or
put it in the command line. It uses the existing approval directory and
replaces the small launcher process with the bridge:

```sh
cd /Users/pavel/dev/film-iq/.worktrees/kaneo-youtrack
.venv/bin/python - <<'PY'
import os
from pathlib import Path

root = Path.cwd()
credential_file = root / '.cache/tracker-poc/private/youtrack-tmdb-live.env'
approval = root / '.cache/tracker-poc/private/tmdb-approval'
catalog = root.parent.parent / '.cache/epic-c/results/reviewed-display-catalog-expanded-20261031.json'
allowed = {'TMDB_API_KEY', 'TMDB_READ_ACCESS_TOKEN'}
credentials = {}
for line in credential_file.read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.lstrip().startswith('#'):
        continue
    name, separator, value = line.partition('=')
    if name not in allowed:
        continue
    if (not separator or name in credentials or not value or not value.isascii()
            or any(char.isspace() for char in value) or value.startswith(('"', "'"))):
        raise SystemExit('TMDB credential configuration is invalid')
    credentials[name] = value
if not credentials or not (approval / 'approved-ids.json').is_file():
    raise SystemExit('TMDB credential or approval file is unavailable')
env = os.environ.copy()
for name in allowed:
    env.pop(name, None)
env.update(credentials)
env['FILMIQ_APPROVAL_DIR'] = str(approval)
env.pop('FILMIQ_REVIEWED_CATALOG', None)
if catalog.is_file():
    env['FILMIQ_REVIEWED_CATALOG'] = str(catalog)
env['PYTHONDONTWRITEBYTECODE'] = '1'
python = str(root / '.venv/bin/python')
os.execve(python, [python, 'docs/research/tracker-poc/tmdb_live.py'], env)
PY
```

Leave this terminal open; **Ctrl-C** stops it, and rerun the block to restart.
Both bridges enforce the existing positive approved-ID list. Loading a film's
live metadata is an explicit UI action and may make multiple upstream calls;
adding a film does not authorize its ID. In this non-pilot configuration, data
is held in page memory and must be loaded again after reload. An unavailable or partial provider response is
unknown, not proof of absence or subscription entitlement. The JSON response
uses `no-store`; that does not establish browser poster-image cache behavior.

The separate MDBList experiment on port 15177 is optional and is not one of the
two TMDB bridges. Its [instructions and unresolved live 403](mdblist.md) are
separate; a successful live ratings response has not been demonstrated.

The reviewed catalog is read from its existing project-local file, with no
copy into either tracker. Kaneo reads it using the optional environment path
above. The existing YouTrack bridge container has that file mounted read-only
using the catalog Compose override; `docker start` retains its mount. Individual
file bind mounts can keep an old file after an atomic source replacement: stop
or recreate the bridge when revoking or replacing the catalog. Stopping the
Kaneo reader likewise disables its catalog access. The UI drops displayed facts
at the recorded expiry. These controls do not purge the pre-existing source or
its backups, and a title match does not independently verify identity.

## Check and stop

To inspect container status and loopback listeners without printing environment
variables or credentials:

```sh
docker ps -a --filter label=com.docker.compose.project=film-iq-tracker-poc --format '{{.Names}} {{.Status}} {{.Ports}}'
lsof -nP -iTCP:15173 -iTCP:15174 -iTCP:15175 -iTCP:15176 -iTCP:18180 -sTCP:LISTEN
```

Stop the UI and preference bridge with Ctrl-C in their respective terminals.
If using the ordinary non-pilot TMDB bridge, stop its foreground terminal too.
The active collection pilot is a background process, so stop it separately:

```sh
.venv/bin/python docs/research/tracker-poc/kaneo_live_pilot.py --stop
```

The command leaves an unrecognized listener untouched. If a copy was launched
elsewhere, identify its owner before stopping it; do not kill an unknown
listener. Then stop only the configured Docker services:

```sh
docker stop film-iq-tracker-poc-tmdb-live-bridge-1
docker stop film-iq-tracker-poc-youtrack-1
docker stop film-iq-tracker-poc-kaneo-1
docker stop film-iq-tracker-poc-postgres-1
```

No container, volume or source file is deleted by these commands. At inspection
on 2026-11-05, the named containers, UI build, interpreter, credential file and
approval file existed; both tracker servers and both TMDB bridges were running.
The foreground start/stop commands and the complete cross-service restart
sequence in this runbook have **not** been executed as a runbook test. A
separate fictional Kaneo database restore/restart passed; live-data backup,
YouTrack recovery, automatic host-reboot startup, Hermes deployment, full poster
cache behavior and streaming entitlement remain unverified. See the
[comparison](comparison.md) and [Kaneo recovery evidence](kaneo-recovery-rehearsal.md).
