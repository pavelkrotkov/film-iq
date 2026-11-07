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

`.venv/bin/python docs/research/tracker-poc/preferences_service_recovery_check.py`
starts a fictional Waitress service on an ephemeral loopback port with the real
preference WSGI application. It previews and saves a preference, restarts the
service, and checks that the preference persists while a preview issued before
restart is rejected. SQLite's online backup runs while the restarted service is
idle; a third service opens the restored database and repeats the assertions.
Kaneo authentication and film access are mocked. This does not test a backup
concurrent with writes, real sessions, or recovery of the live database.

The pinned Kaneo API describes task image uploads as presigned object-storage
uploads. In the running local POC, the S3 bucket, endpoint, region, access key
and secret key variables were all absent; no configuration values were printed.
In the separate fictional recovery instance, an authenticated request to start
an image upload returned HTTP 503 with no object storage configured. No bytes
were uploaded. This check did not issue an upload request against the real film
project.

### Attachment backup and restore with fictional object storage

On 2026-11-06, a separate fixture used Kaneo 2.49.0, PostgreSQL 16 and
[Garage v2.5.0](https://garagehq.deuxfleurs.fr/documentation/quick-start/)
as an S3-compatible object store. The official `dxflrs/garage` image was pinned
to digest `sha256:677e5b758e4425a325b811c425c026bf35a4bf42f7ddbaa773de3f4fd779a5a5`;
Garage is AGPL-3.0 and was used only in this fixture. Its documented
single-node/default-bucket mode has no replication and is not a production
storage recommendation. Source and restored services used separate internal
Docker networks, project-local bind mounts and no published ports. Credentials,
the authenticated API user, image and task were newly generated fictional
fixture data. No browser session, live tracker, Movary or metadata provider was
accessed.

The source Kaneo API presigned an image PUT, finalized the object, saved the
asset reference on a fictional task and returned the exact PNG bytes. After
stopping the source app and object store, the fixture took a PostgreSQL dump and
separately copied the stopped object store's complete metadata and data files to
a new project-local backup. A database-only restore into a separate fixture
returned HTTP 404 for the original asset. As a control, the same restored app
and empty store successfully uploaded, finalized and read a second fictional
image first, establishing that credentials and the object-store path worked.
The control created one unlinked asset record in the fictional destination DB;
its object remains in the separate stopped empty-store fixture. This verifies
the target asset, not that every row in the modified destination DB has a
backing object.

After restoring the copied object store, the restored app returned the original
task reference and exactly matching image bytes. The same checks passed after
restarting both the restored app and object store. This is a stopped-writer,
single-node filesystem-copy rehearsal for one fictional object; it is not a
verified Garage production backup procedure, a concurrent-write test, an
off-machine backup, or recovery of the existing POC. In particular, the existing
Kaneo POC still has no configured object storage, so attachment upload there
remains unavailable.

The successful fixture directory and backups remain under
`.cache/tracker-poc/private/`; its seven containers were stopped and retained.
One `du` sample was 108 MiB for the fixture directory, including a 1.5 MiB
backup. The image's local uncompressed size was 97,099,512 bytes; runtime peak
memory was not measured. These figures are not a capacity estimate.

To repeat with fresh fictional directories from the worktree root, first ensure
Docker is running and the pinned PostgreSQL and Kaneo images in
`kaneo-attachment-fixture/compose.yaml` are already present. Download the pinned
Garage fixture image if necessary, then run:

```sh
docker pull dxflrs/garage@sha256:677e5b758e4425a325b811c425c026bf35a4bf42f7ddbaa773de3f4fd779a5a5
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/kaneo_attachment_recovery.py
```

The runner validates its Compose service names, project-local bind mounts,
internal networks and absent published ports before creating containers. It
leaves the generated fixture directory and stopped containers in place. It
does not download provider data or alter the currently running POCs.

An additional fictional API round-trip ran the actual Python enrichment
adapter against the internal-network recovery instance. It created one new
fictional task, repeated its import, changed a complete provider observation,
and verified that subscriptions, rentals and purchases remain separate.
Partial and failed fixture responses preserved the prior observation and the
edited synopsis and lifecycle. The test uses a fresh API-only login created
inside the fixture container and kept in memory; it does not use a browser
session or call a metadata provider. It exercises the adapter with a local RPC
transport; it does not test the real POC's authentication or personal records.

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
docker compose -f "$REHEARSAL_DIR/compose.yaml" exec -T source-app node - < docs/research/tracker-poc/kaneo-recovery-fixture/image-config-check.js
.venv/bin/python docs/research/tracker-poc/kaneo_fixture_enrich_live_check.py --fixture-app "${COMPOSE_PROJECT_NAME}-source-app-1"
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
