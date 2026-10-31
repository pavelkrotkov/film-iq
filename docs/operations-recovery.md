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
