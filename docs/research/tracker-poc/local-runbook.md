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
[localhost:15173](http://localhost:15173/auth/sign-in), using the existing POC
account, then open its film UI at [localhost:15174](http://localhost:15174/).
Sign in to [YouTrack](http://localhost:18180/) with the existing administrator
account and open **FilmIQ POC** from the main menu. The installed YouTrack app
runs inside YouTrack; it does not use the separate Kaneo UI server.

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

The Kaneo bridge is a **third foreground terminal**. The command below reads
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
env['PYTHONDONTWRITEBYTECODE'] = '1'
python = str(root / '.venv/bin/python')
os.execve(python, [python, 'docs/research/tracker-poc/tmdb_live.py'], env)
PY
```

Leave this terminal open; **Ctrl-C** stops it, and rerun the block to restart.
Both bridges enforce the existing positive approved-ID list. Loading a film's
live metadata is an explicit UI action and may make multiple upstream calls;
adding a film does not authorize its ID. Data is held in page memory and must
be loaded again after reload. An unavailable or partial provider response is
unknown, not proof of absence or subscription entitlement. The JSON response
uses `no-store`; that does not establish browser poster-image cache behavior.

The separate MDBList experiment on port 15177 is optional and is not one of the
two TMDB bridges. Its [instructions and unresolved live 403](mdblist.md) are
separate; a successful live ratings response has not been demonstrated.

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
