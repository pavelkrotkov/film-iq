# Offline recovery and disposable-cache policy

C8 #26 supplies small offline primitives, not a verified production deployment.
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

C8 stays open. A complete Movary backup must include its database, storage,
configuration and pinned application version; a live restore needs explicit user
authorization and an isolated target agreed with the user. No Movary export,
backup, service stop, restore or new retention decision is claimed by this PR.
Actual selected C1/C4/C5 integration, rights/quotas and an observed production
failed-job recovery still require acceptance.

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
