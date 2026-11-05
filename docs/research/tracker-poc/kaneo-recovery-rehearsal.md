# Fictional Kaneo recovery rehearsal

On 2026-11-05, a fresh Kaneo 2.49.0 and PostgreSQL 16 fixture ran on a
separate Docker internal network with a new bind-mounted database beneath
`.cache/tracker-poc/ops-rehearsal-20261105-a/`. The effective Compose config
and actual container mounts/networks were checked before use. Internal Docker
networks did not publish their configured loopback ports on this Docker Desktop
installation; API checks used `docker exec`, without adding an external network.
No live POC database, Movary data, or external metadata service was accessed.

One fictional user, workspace, project and film were created through Kaneo's
API. A numeric custom field, synopsis, `in-progress` lifecycle and comment were
read back. `pg_dump -Fc` produced a 137,479-byte archive, mode 0600; a fresh,
separate PostgreSQL destination had zero public application tables before
`pg_restore --exit-on-error`. A new Kaneo instance authenticated and read the
same fictional values. After restarting that restored Kaneo container, the same
API assertions passed again. The four fixture containers were stopped; data,
configuration and the archive remain in the ignored project-local directory.
A single sample showed approximately 491 MiB combined container memory, and
`du` reported 100 MiB for the fixture directory. These are not a benchmark.

A second fresh run used the checked-in fixture templates and newly generated
credentials. It repeated the source, restore and post-restart assertions. The
explicit readiness wait shown below was then checked against that restored
instance before its two containers were stopped.

This demonstrates a database restore for one fictional record and the fixture's
login configuration. It does **not** establish a backup of the live POC,
attachments, separately stored SQLite preferences, Movary sidecar, auth-secret
recovery, deletion of retained provider data, host reboot auto-start, or
recovery after a PostgreSQL/container/host failure. A database dump does not
include PostgreSQL cluster-wide roles or external files. Secret values are not
included in the dump. The fictional credentials and fixture configuration are
not for another deployment.

Separately, `uv run python docs/research/tracker-poc/preferences_recovery_check.py`
creates a fictional preference database in WAL mode, uses SQLite's online
backup to make a mode-0600 archive, restores it to a second database and checks
the exact score, unknown watchlist, watched timestamp and note through the POC
load function. This is an offline one-record check, not a service-restart,
concurrent-write or live-data recovery test. Its fictional files remain in a
new ignored project-local directory.

## Repeat with fresh fictional directories

Run from this worktree root. The pinned images must already be local. These
commands create new files under the selected project folder, use new random
fixture secrets, and never copy either live database. The version-controlled
fictional fixture config and test script are used as templates. Each run uses a new
Compose project name. It leaves its own files and containers in place; stopping
is reversible and is not deletion.

```sh
export REHEARSAL_ID="$(python3 -c 'import secrets; print(secrets.token_hex(6))')"
export REHEARSAL_DIR=".cache/tracker-poc/recovery-replay-$REHEARSAL_ID"
export COMPOSE_PROJECT_NAME="filmiq-recovery-$REHEARSAL_ID"
python3 - <<'PY'
from pathlib import Path
import os, secrets, shutil
root = Path(os.environ['REHEARSAL_DIR'])
root.mkdir(mode=0o700)  # fail if it already exists
for name in ('source-db', 'restored-db', 'archive'):
    (root / name).mkdir(mode=0o700)
template = Path('docs/research/tracker-poc/kaneo-recovery-fixture')
for name in ('compose.yaml', 'fixture.js'):
    shutil.copyfile(template / name, root / name)
(root / 'fixture.js').chmod(0o600)
password, secret, fixture_password = secrets.token_hex(24), secrets.token_hex(32), secrets.token_urlsafe(24)
for name, port in (('source', 25173), ('restored', 25174)):
    path = root / f'{name}.env'
    path.write_text(f'KANEO_CLIENT_URL=http://localhost:{port}\nCORS_ORIGINS=http://localhost:{port}\nPOSTGRES_DB=kaneo\nPOSTGRES_USER=kaneo\nPOSTGRES_PASSWORD={password}\nAUTH_SECRET={secret}\nFIXTURE_PASSWORD={fixture_password}\n')
    path.chmod(0o600)
PY
```

Before starting containers, assert the fully resolved configuration. Do not
print it: Compose expands the private fixture secrets. Also check both specified
loopback ports are unused (`lsof -nP -iTCP:25173 -iTCP:25174 -sTCP:LISTEN`;
no output means no listener). Stop if any assertion fails.

```sh
docker compose -f "$REHEARSAL_DIR/compose.yaml" config --format json | python3 -c '
import json, os, pathlib, sys
d = json.load(sys.stdin); root = pathlib.Path(os.environ["REHEARSAL_DIR"]).resolve(); s = d["services"]
assert d["name"] == os.environ["COMPOSE_PROJECT_NAME"]
assert set(s) == {"source-db", "source-app", "restored-db", "restored-app"}
assert all(d["networks"][n]["internal"] is True for n in ("source", "restored"))
assert all(set(s[n]["networks"]) == {k} for n,k in (("source-db","source"),("source-app","source"),("restored-db","restored"),("restored-app","restored")))
assert all(len(s[n]["volumes"]) == 1 and pathlib.Path(s[n]["volumes"][0]["source"]) == root/n for n in ("source-db","restored-db"))
assert all("volumes" not in s[n] for n in ("source-app","restored-app"))
assert all(len(s[n]["ports"]) == 1 and s[n]["ports"][0]["host_ip"] == "127.0.0.1" and str(s[n]["ports"][0]["published"]) == port for n,port in (("source-app","25173"),("restored-app","25174")))
print("Fixture isolation configuration passed.")'
```

Start source and destination database; inspect their actual bind paths and
networks against the new project directory before creating data or restoring.
Only proceed if the destination public schema has no application tables.

```sh
docker compose -f "$REHEARSAL_DIR/compose.yaml" up -d --pull never --wait --wait-timeout 90 source-app restored-db
for service in source-db restored-db; do
  docker inspect "$(docker compose -f "$REHEARSAL_DIR/compose.yaml" ps -q "$service")" --format '{{json .Mounts}} {{json .NetworkSettings.Networks}}'
done
# Verify the output names only the matching new source-db/restored-db paths
# and their respective isolated networks; no live POC mounts or networks.
test "$(docker compose -f "$REHEARSAL_DIR/compose.yaml" exec -T restored-db psql -U kaneo -d kaneo -Atc "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p');")" = 0
docker compose -f "$REHEARSAL_DIR/compose.yaml" exec -T source-app node - create < "$REHEARSAL_DIR/fixture.js"
umask 077
docker compose -f "$REHEARSAL_DIR/compose.yaml" exec -T source-db pg_dump -U kaneo -d kaneo -Fc > "$REHEARSAL_DIR/archive/fixture.dump"
docker compose -f "$REHEARSAL_DIR/compose.yaml" exec -T restored-db pg_restore -U kaneo -d kaneo --exit-on-error < "$REHEARSAL_DIR/archive/fixture.dump"
docker compose -f "$REHEARSAL_DIR/compose.yaml" up -d --pull never --wait --wait-timeout 90 restored-app
docker compose -f "$REHEARSAL_DIR/compose.yaml" exec -T restored-app node - verify < "$REHEARSAL_DIR/fixture.js"
docker compose -f "$REHEARSAL_DIR/compose.yaml" restart restored-app
docker compose -f "$REHEARSAL_DIR/compose.yaml" up -d --pull never --wait --wait-timeout 90 restored-app
docker compose -f "$REHEARSAL_DIR/compose.yaml" exec -T restored-app node - verify < "$REHEARSAL_DIR/fixture.js"
docker compose -f "$REHEARSAL_DIR/compose.yaml" stop
```

Never substitute a live database, directory, existing
Compose project, or backup into these commands.
