# Kaneo watched snapshot refresh candidate

`kaneo_watched_refresh.py` prepares a current user's Movary watched sidecar
from an already-completed, project-local Movary snapshot and its adjacent
`.status` file. It does not contact Movary, modify tracker records or editable
preferences, or use a browser session. The independent Kaneo API key must be
provided in the process environment as `KANEO_API_KEY`; do not put its value
in a command, chat, or Git. The account's key scope must permit reading the
current user, the project, its fields and tasks. A key has not been provisioned
or tested on the real POC.

The key owner must already exist in the sidecar. The refresh checks complete
source provenance, unresolved events, the stored project, all project TMDb
identity values, and each watched film's current task and identity field.
Duplicate, missing, inaccessible or changed mappings stop the refresh. It
preserves other users. A newer complete source can add, remove or change
watched events; this does not independently verify film identity. The visible
UI still treats absence from the snapshot as unknown.

Preview is the default. For a changed observation, `--apply` requires a **new**
backup path in an owner-only project directory. It writes the exact previous
sidecar there with mode 0600, rechecks the current sidecar, atomically writes
the replacement and checks readback. An unchanged repeat makes no backup or
write. Run one sidecar writer at a time: the recheck is not an atomic
compare-and-swap. If a failure or timeout occurs, inspect the sidecar and the
private backup before retrying. A backup file contains personal watched history
and must remain private. This is not a full tracker or server backup.

With a separately provisioned key already in the environment, preview a
complete private snapshot and its adjacent `.status` file, then use a new
backup path if applying:

```sh
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python docs/research/tracker-poc/kaneo_watched_refresh.py --snapshot .cache/tracker-poc/private/your-snapshot.json
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python docs/research/tracker-poc/kaneo_watched_refresh.py --snapshot .cache/tracker-poc/private/your-snapshot.json --apply --backup .cache/tracker-poc/private/your-new-backup.json
```

## Current same-content observation

On November 6, 2026, the later complete read-only Movary snapshot had the same
27 watched IDs and ordered event arrays, and the same empty unresolved history,
as the existing Kaneo sidecar. A separately reviewed one-time offline procedure
required a single existing sidecar owner, the configured project, complete
source provenance and exact event equality. It saved an owner-only byte-for-byte
backup, then replaced only the unique observation timestamp in the sidecar.
Readback confirmed every other byte, including all watched data, was unchanged.
The private backup is `.cache/tracker-poc/private/kaneo-watched-before-same-content-20261106.json`;
the source snapshot remains under the same private directory. Neither tracker
nor Movary was modified. This assumes one sidecar writer and is
continuity evidence, not independent verification that the two snapshots came
from the same account. Browser display of this update has not been tested.

That narrow same-content operation cannot import changed watched history. Use
the separately authenticated, dry-run-first bearer path above for a later
complete observation that changes watched membership or events; its real POC
credentials and apply path remain unverified.

Fictional checks:

```sh
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python docs/research/tracker-poc/kaneo_watched_refresh_check.py
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python docs/research/tracker-poc/kaneo_watched_refresh_cli_check.py
```

Fictional CLI tests exercise preview, exact backup, update, readback, a second
user, an unchanged retry and an intervening-sidecar-change refusal. An
isolated pinned Kaneo 2.49.0 server test independently issued a fictional API
key, discarded its API-only setup session, confirmed `/user/me` identified the
key owner and used the bearer key to prepare one watched mapping from fictional
data. The server fixture does not apply a sidecar write or exercise the CLI
environment argument. The real POC has not been authenticated or refreshed by
this candidate.
