# Offline recovery and disposable-cache policy

C8 #26 supplies offline recovery primitives; dated operational acceptance is
recorded below. Earlier pending statements describe their observation time.
Run Python 3.12+ with `uv sync --dev`; SQLite must pass the existing patched-WAL
version gate. Keep databases, exports, comments, ratings, secrets, backups and
reports in ignored private directories inside the selected project folder.
Never run two scheduled writers against the same installation. Existing B4
collection jobs are separately configured and are not changed here.

## Film-IQ recovery

`film_iq.recovery.backup(db, Path(...))` uses SQLite's online backup API, including
committed WAL state, and validates integrity and foreign keys before/after copy.
Commit or roll back first. The destination must be new; mode is 0600.
`restore(backup_path, new_database_path)` opens the backup read-only and restores
to a new file. It never overwrites a running database. Open the restored path
with `storage.connect`, apply `migrate`, validate and replay accepted evidence
before an operator switches an installation to it. Preserve the original backup
until acceptance; do not consolidate or relocate user records without agreement.

The deterministic restore exercise checks schema and accepted revision/match
replay without duplicate observations or votes. C1 separately exercises a killed
process/transaction restart and last-success cursor preservation. These tests use
synthetic disposable databases, not the running Movary installation.

## Rights and cache deletion

`CachePolicy` records an explicit permission decision, source, attribution,
rights evidence, timezone-aware expiry, termination flag and policy version.
Unknown permission is `allowed=False` and reports `blocked`; it is not permission
to create a cache. Expiry or termination is `purge_due`.
`cache_purge.purge(root, names, policy, now)` previews named disposable files;
`execute=True` deletes only those names within the explicitly supplied cache
root. No source scan or live deletion occurs automatically. Backups and reports
that retain restricted content require the same retention assessment; this helper
does not discover copies or certify a provider-compliance program.

TMDB's observed terms specify a six-month cache ceiling and termination purge;
use an expiry no later than that ceiling (180 days is a conservative local
choice). This ceiling is not a grant of the intended use: broader AI/commercial
applicability and third-party rights remain unresolved. Movie of the Night has
attribution/third-party and AI-model-use restrictions. See
[the rights follow-up](research/availability/rights-20261030.md) and
[Gate B](research/gate-b.md). No production provider history is enabled here.
Provider-specific acquisition must enforce the reviewed permission and deadline
before storing data, then include all retained copies in a deletion plan.

Current opt-in HTTP transports use bounded timeouts and a single attempt rather
than unbounded retries; real quotas and production polling remain gated on
B4/B8.

## One scheduled private run

`uv run python -m film_iq.operations` connects the existing read-only Movary
refresh, accepted-evidence discovery report and online Film-IQ database backup.
It requires `--database`, `--cohort`, `--snapshot`, `--report`, `--backups` and
`--status` paths, plus the same two complete CSV or exporter-command options
as `refresh-movary`. The three `MOVARY_*` credentials stay in the process
environment. Use absolute paths inside the selected project for scheduling.
The cohort must already have independently accepted source/identity evidence;
this command does not accept a pending import or add films to Movary.

For example, after privately loading credentials and setting complete export
commands as JSON argv arrays:

```sh
uv run python -m film_iq.operations \
  --database .cache/private/evidence.db --cohort .cache/private/cohort.json \
  --snapshot .cache/private/snapshot.json --report .cache/private/discovery.md \
  --backups .cache/private/backups --status .cache/private/run.status \
  --ratings-command "$RATINGS_COMMAND" --history-command "$HISTORY_COMMAND"
```

The status path identifies the installation: all its scheduled invocations
must use that same absolute path. A nonblocking native file lock rejects an
overlapping run without reading Movary or replacing status. Do manual imports
with that schedule disabled, rather than running a second writer. The lock
releases when a process exits or is killed; no lock-file deletion is needed.
This command works on Linux/macOS, where `fcntl.flock` is available.

Register this exact command with the host's existing native scheduler (cron,
systemd timer or launchd); no Python scheduler or daemon is needed. Set its
working directory to the selected project, use the absolute `uv` executable,
set `umask 077`, privately load credentials, and send routine output to a
private log. A daily or weekly schedule is a user/operator choice, not a
provider polling recommendation. This run makes only the five existing
personal-data reads; it performs no production-provider polling. Existing B4
jobs are independent and must not be edited or repurposed.

Status is marked stale **before** work begins and records the last successful
run separately. An interruption therefore cannot claim freshness. A failed
refresh preserves the prior snapshot, and any later failed step preserves the
prior report; status remains stale with a generic error that contains no
private response or credential. The personal snapshot may be newer than the
retained report after a later-step failure. Check run status before using the
report. Fix the failed input and rerun the same command; do not clear state or
re-import evidence. A successful retry atomically publishes a mode-0600 report,
creates a new validated evidence backup and clears stale state. Backups are
never silently overwritten or automatically deleted.

The run's evidence backup is **not** a complete installation archive. Preserve
private personal snapshots/status, curated inputs, operator config/secrets,
the deployed Git revision and `uv.lock` alongside it under their respective
rights/retention policies before claiming complete Film-IQ recovery. Production
source/provider storage is still gated as described above.

## Remaining production acceptance

The authorized complete Movary recovery is now verified for the captured
installation, as recorded in the latest acceptance below. Earlier statements
that its authorization/test were pending are historical. Production-provider
rights, quotas and adoption remain separate requirements; this recovery does
not adopt a provider feed or certify unrestricted retention.

### Live deployment inspection — 2026-10-31

Read-only inspection found the running Movary image pinned to
`leepeuker/movary:0.82.1`, a healthy application container and SQLite 3.53.4.
The deployment's storage is a bind mount containing `movary.sqlite`, `app`
and `logs`. No personal contents or credentials are published here.

The [pinned upstream recovery guide](https://github.com/leepeuker/movary/blob/0.82.1/docs/backup-and-restore.md)
requires stopping Movary and its worker before copying complete storage,
preserving config/secrets and the application version, then restoring into an
isolated target, recreating `storage:link`, checking `database:migration:status`
and verifying application/worker operation. A running SQLite file copy is not
a valid substitute. A separately scoped service interruption and isolated
target/storage authorization remain required; no stop, backup, restore or
personal-data write was performed by this inspection.

## Read actual operational status

`film-iq status` replaces the former static POC message. Supply only the private
paths to inspect; omitted components remain `not_configured`:

```sh
uv run film-iq status --run-status .cache/private/run.status \
  --snapshot .cache/private/snapshot.json --database .cache/private/evidence.db \
  --catalog .cache/private/reviewed-display.json --format json
```

The default text output and JSON share the same allowlisted facts: operation
last-successful time, personal snapshot/status generation consistency, source
attempt/error/running counts and last-successful cursor time, catalog expiry,
and explicit permitted/blocked/purge-due provider policy counts. Raw cursors,
source names, film data, ratings, comments, rights text, paths and exception
payloads are not printed. This command makes no network call, requires no
credentials and opens an existing SQLite database with `mode=ro`; it never
creates a missing database, migrates, repairs or purges anything.
Native SQLite read-only WAL access may create `-wal`/`-shm` coordination files;
read-only refers to database contents, not a guarantee of zero filesystem
activity. A directory that cannot provide required WAL coordination may report
`invalid`. Do not use `immutable=1` for a potentially live WAL database.

Exit 1 means a configured input is missing/invalid, stale, expired/not-yet-valid,
or has acquisition/policy state needing attention. Exit 0 means no such
condition was observed; omitted configuration is still unknown, not healthy.
`current` means a supported successful status (and matching personal generation),
not a claimed refresh interval or release acceptance. Successful times are shown
in UTC; no arbitrary age threshold is invented. Use optional timezone-aware
`--now` for a reproducible catalogue/policy expiry assessment. The command does
not prove a scheduler is registered, a provider feed adopted or a full
installation restored.

## Complete selected collection

Repeat `--cohort` on `python -m film_iq.operations` for every independently
accepted ballot in the installation. The same complete-cohort validation,
reviewed-work deduplication and personal freshness checks used by `discover`
apply to the scheduled report. Repeated arguments accumulate; later ballots
never silently replace earlier ones. The Python API also accepts a single Path
for existing callers or a list of Paths for a collection.

A real private read-only acceptance run completed refresh/report/backup, then
reproduced an export-command failure and successful retry. The failure retained
the previous snapshot/report bytes, successful timestamp and acquisition state,
while both freshness markers became stale. Retry produced a matching fresh
snapshot/status and a new successful timestamp. The resulting evidence backup
restored to a disposable database with passing integrity, foreign-key, schema
and cursor checks; files were mode0600. Private commands and receipts remain
inside the selected project's ignored cache. This does not establish complete
Movary installation restoration, which still requires the separately requested
service-stop/isolated-restore authorization, or production provider acceptance.

### Actual bounded Film-IQ installation restore — 2026-10-31

A private schema10 installation at Git revision `0fcc05e` was archived and
restored into a separate project-local directory. The archive included a native
online evidence backup, the pinned Git source archive and `uv.lock`, selected
cohort/source-audit inputs, reviewed catalog, personal snapshot/status and private
operator configuration. Restored file hashes matched; SQLite integrity and
foreign-key checks passed. The restored application CLI consumed only restored
inputs and reproduced the complete original discovery JSON semantically, with
no external calls or Movary actions. Private archive/receipts remain inside the
selected project's ignored cache; copied metadata retains its expiry and usage
restrictions, including archive copies.

This verifies recovery of that selected schema10 Film-IQ installation. Later
schema/input changes require their own recovery check. It does not verify
Movary database/storage/config/version restoration, which remains pending the
separately scoped service-stop/isolated-restore authorization, or production
provider adoption/permissions.

### Actual selected collection and native scheduling — 2026-10-31

After a pre-migration backup, the actual selected evidence database advanced to
schema11 using the reviewed typed-recognition implementation at `fdba280`.
The 24 accepted cohorts contain 114 source facts: 47 critic selections, 50
Registry selections and 17 award outcomes. There are 112 reviewed work mentions
representing 106 distinct reviewed works; two source entries remain unresolved.
These are explicitly selected cohorts, not complete publisher/world coverage.
Identical replay of all 24 imports preserved semantic evidence, historical
critic snapshots and existing critic values; canonical typed-component snapshot
replay also passed. No reception values or personal opinions were invented.

The exact native operations command then completed read-only personal refresh,
the full selected-collection report and evidence backup. The private launchd
job `com.filmiq.discovery.daily` is now registered in the current user's GUI
domain for 10:30 local time, with `RunAtLoad` disabled. An explicit native
kickstart completed one observed run with exit 0, a fresh successful run status
and an idle/nonrunning final job state. This verifies registration and one
native execution, not a future calendar firing or reboot/login persistence.
Private configuration, commands, logs and receipts stay in the selected project.
No personal account counts/values or credentials are published here.

No provider polling, Movary writes or existing B4 job changes accompanied these
operations. Complete Movary recovery, genuine personal rating/comment-edit
acceptance and the time-separated B4/B8 production-provider gate remain pending.

### Schema11 recovery and actual status follow-up — 2026-10-31

The selected schema11 Film-IQ installation at merged revision `4ce74ba` passed
its own archive/isolated-restore check after the typed collection and status CLI
were integrated. Restored file hashes, SQLite integrity and foreign keys passed;
the restored application CLI reproduced the complete discovery JSON semantically
using only restored inputs, with zero external calls or Movary actions. Private
archive/receipt files remain inside the selected project's ignored cache. The
copied catalog retains its original 2027-04-29 expiry; restoration does not renew
metadata rights or retention deadlines.

The merged status CLI was also inspected against all configured private inputs:
operations and personal generations were current, acquisition was observed,
catalog facts were fresh and provider policies were not configured. This is an
observed component summary, not a release-health or production-provider claim.
Complete Movary database/storage/config/version restoration, genuine personal
score/comment edits and the B4/B8 production-provider decisions remain separate
outstanding acceptance requirements.

## Reinstall the restored application with its captured lock

Use an existing compatible `uv` executable and a provided Python 3.12+ whose
SQLite passes the application's patched-WAL version gate. The example below
keeps the restored application, cache and temporary files inside an
operator-selected project. Restore the installation archive first, then use
its captured `uv.lock`; do not resolve a new dependency set during recovery.

```sh
(
set -e
FILMIQ_PROJECT=/absolute/path/to/selected/project
FILMIQ_RESTORE="$FILMIQ_PROJECT/.cache/recovery/isolated-restore"
FILMIQ_APP="$FILMIQ_RESTORE/application"
FILMIQ_PYTHON=/absolute/path/to/python3.12
export UV_CACHE_DIR="$FILMIQ_PROJECT/.cache/uv"
export TMPDIR="$FILMIQ_PROJECT/.cache/recovery-tmp"
export UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
export UV_PROJECT_ENVIRONMENT="$FILMIQ_APP/.venv"
mkdir -p "$UV_CACHE_DIR" "$TMPDIR" "$FILMIQ_APP/.cache"
cp "$FILMIQ_RESTORE/inputs/uv.lock" "$FILMIQ_APP/uv.lock"
uv sync --project "$FILMIQ_APP" --frozen --offline --dev --python "$FILMIQ_PYTHON"
  cd "$FILMIQ_APP" || exit 1
  unset MOVARY_INTEGRATION
  uv run --frozen --offline ruff check .
  uv run --frozen --offline ruff format --check .
  uv run --frozen --offline ty check .
  uv run --frozen --offline pytest --basetemp "$FILMIQ_APP/.cache/pytest-restore"
)
```

Offline installation requires all locked packages and build requirements to be
present in the selected uv cache; a new empty cache is not sufficient. This
procedure does not establish a clean network bootstrap on arbitrary hosts.
`MOVARY_INTEGRATION` must be unset for credential-free tests: the opt-in test
treats any nonempty value, including `0`, as enabled. Creating the explicit
pytest basetemp parent avoids a test-driver directory error.

Finally run the fresh `$FILMIQ_APP/.venv/bin/film-iq discover` with every selected
cohort and the database, snapshot/status and catalog paths mapped to restored
inputs from the archive manifest. Do not reuse live installation paths. Compare
the complete parsed JSON to the captured expected report; ordering/formatting
of JSON object keys alone is not a behavioral difference. Keep personal inputs
and comparison output private under their original retention rules.

### Actual fresh-environment acceptance — 2026-10-31

The restored schema11 application at captured revision `4ce74ba` was installed
into a fresh virtual environment using its unchanged lock and the existing
private offline cache. CPython 3.12.15 installed 45 packages including the editable
application. Ruff check/format and ty passed; pytest passed 544 tests with one
opt-in skip. The freshly installed CLI then consumed all 24 selected cohorts
and only restored inputs, reproducing the full discovery JSON semantically.
No external calls or Movary actions occurred.

The initial acceptance driver failed because its explicit basetemp parent was
absent and it set the truthy opt-in flag to `0`; the resulting live-test setup
failed before I/O. The private failure log was retained. Creating the parent
and unsetting the flag corrected the driver without changing product code.
This verifies the captured installation on the tested host/cache, not all hosts
or a complete Movary restore. Genuine personal-edit acceptance and production
provider/B4/B8 decisions remain outstanding.

### Observed digest baseline and post-planner restore — 2026-10-31

The actual changes CLI at merged C7 revision `eedd73b` completed a preview that
created no checkpoint, an explicit acknowledgement establishing the 24 accepted
source-scope baseline, and a repeat with zero pending changes. No historical
alert or real source/offer transition was fabricated. The checkpoint retained
only opaque IDs and revision pointers; both it and the baseline report were
mode 0600. Evidence database bytes were unchanged. No production provider policy
was configured for this check.

The selected installation archive at post-planner revision `8a724c1` included
the changes checkpoint and baseline report. Its isolated restore passed file
hashes, SQLite integrity and foreign keys, and the restored application CLI
reproduced the full discovery JSON semantically. Restored changes preview
returned no duplicates without changing its checkpoint. There were no external
calls or Movary actions; copied catalog data retained its original 2027-04-29
expiry. Private archives/receipts remain in the selected project's ignored
storage. This verifies the observed baseline/recovery behavior, not actual
delivery of live transitions, complete Movary restoration, production providers
or genuine user rating/comment edits.

### Completion observed at the configured daily time — 2026-10-31

A later read-only native-job inspection found two completed runs, last exit 0
and an idle job. Its second successful completion was 14:30:03 UTC (10:30 local),
matching the registered daily calendar time; native stdout, run status and the
personal snapshot/status generation agreed. This corroborates execution at the
configured time, without asserting the trigger's provenance or reboot/login
persistence. The inspection changed no jobs, accounts, databases or B4 settings.

The refresh/report implementation supports absent personal scores correctly;
genuine nonempty score/comment changes are still unobserved real-user acceptance
cases. Complete Movary recovery remains pending its separately scoped approval
and test, and production-provider requirements remain gated independently. These
limits do not require another user source audit or invented personal ratings.

### Authorized complete Movary recovery — 2026-10-31

With explicit user approval, the original Movary application and its background
worker were stopped together. An exit trap and independent restart fallback
protected the original service. Complete stopped SQLite storage, application
files/logs, deployment configuration/secrets, effective environment and the exact
running image were captured privately inside the selected project. The original
service was healthy again after approximately six seconds and passed a final
health check. No running SQLite file copy or live personal-data edit was used.

The separate restore used the captured Movary 0.82.1 image, project-local writable
bind mounts, a read-only container root, disabled container logging, no published
ports and no network access. Original storage file hashes matched; integrity and
foreign-key checks passed. Every original database table matched the backup
before authenticated reads. Native storage linking, current migration status,
application and background-worker startup passed. The preserved account token
read complete played/history/watchlist collections, and native ratings/history
exports succeeded. Authenticated API reads update the clone token's last-use
metadata; the pre-read comparison distinguishes that expected change.

After preservation checks, the supported native CLI created a disposable account
only in the offline clone. Native CSRF/session login and a protected account page
succeeded. The original users' stored password hashes were preserved; their
plaintext-password sign-in was not tested. The clone was removed after acceptance;
private backups and receipts remain in the selected project's ignored storage
under existing retention restrictions. No production-provider requests, original
account changes or B4 job changes accompanied this exercise.

## Explicit retained-copy inventory and purge procedure

A copied report/export, online database backup, archive and extracted/restored
copy retain the earliest deadline of every restricted input they contain.
Copying, restoring, replaying an old observation or renewing a source policy
must not reset that deadline. A mixed-source archive containing an expired
source must be removed as a whole unless a separately reviewed replacement
excludes that content; unrelated primary source rows can remain.

For future managed copies, keep a private, explicit inventory alongside operator
configuration: source IDs, original earliest expiry, policy version/termination
decision and each exact relative filename under the agreed private cache root.
Include the archive, extracted backup and restored database as separate names.
This is an operator-maintained record, not automatic artifact discovery. Do not
infer permission to delete personal archives or unrelated files. Obtain the
necessary scope before executing against actual retained copies.

For an explicitly expired or terminated policy, first call
`cache_purge.purge(root, names, policy, now)` and
`availability.policies.purge_source(db, source, now)` without `execute`; compare
both previews to the approved inventory. Only then call both with
`execute=True`, verify each named file is absent and the source ledger data is
removed, and check unrelated source rows/user-owned files remain. Open database
copies must be closed before deleting their names. A denied/unknown permission
is `blocked`, not invented termination or permission for arbitrary deletion.
The file helper accepts named files, never a directory tree; neither helper
finds unlisted copies, rewrites mixed backups or schedules cleanup.

The synthetic retained-copy regression exercises reports/exports, a validated
online backup, an archive, its extracted backup and an isolated restored copy.
Both expiry and explicit termination preview without deleting, then remove all
named affected copies and source rows while preserving unrelated primary rows
and a user-owned sentinel. Backup/restore and identical reimport preserve the
original observation expiry despite a later policy deadline. This is tested
readiness for an explicit inventory, not a claim that real copies were purged or
that a production provider policy has been adopted.
