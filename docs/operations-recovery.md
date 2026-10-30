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
B4/B8. No job broker or new scheduler is needed for these primitives.

## Remaining production acceptance

C8 stays open. A complete Movary backup must include its database, storage,
configuration and pinned application version; a live restore needs explicit user
authorization and an isolated target agreed with the user. No Movary export,
backup, service stop, restore or new retention decision is claimed by this PR.
Actual selected C1/C4/C5 integration, rights/quotas and an observed production
failed-job recovery still require acceptance.
