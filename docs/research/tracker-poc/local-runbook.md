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
`.cache/tracker-poc/private/youtrack-pilot-rollback-i792iwgg/`. Restore them
only by updating the two existing apps in place; deleting an app deletes its
app-owned data. Recreating the original bridge also requires the original
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

For the three foreground terminals, use Ctrl-C in each terminal. If an older
copy was launched elsewhere, identify its owner before stopping it; do not kill
an unknown listener. Then stop only the configured Docker services:

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
