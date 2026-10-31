# Local offer observation ledger

The provider-neutral ledger records a reviewed source's observations, its latest
complete comparable snapshot and source-specific change events. It does not
fetch a provider, choose a production feed, establish rights, or infer personal
account entitlement. Production use still requires B4/B8 and provider-specific
approved use, quotas, attribution and retention limits.

Register an explicitly reviewed `CachePolicy` JSON, then import a `Fetch` JSON:

```sh
uv run python -m film_iq.availability.store_command policy --database private.db --input reviewed-policy.json --now 2026-10-31T12:00:00Z
uv run python -m film_iq.availability.store_command import --database private.db --input observation.json --now 2026-10-31T12:00:00Z
uv run python -m film_iq.availability.store_command state --database private.db --input observation.json --now 2026-10-31T12:00:00Z
```

A policy requires exact source ID, boolean `allowed`, `rights_evidence`,
`attribution`, timezone-aware `expires_at`, and optional boolean `terminated`.
It is an explicit review decision, not a permission discovered from public access.
Set the deadline from the actual permitted source terms before import: this
provider-neutral command does not grant six months to every source or clear
TMDB/other providers' AI/commercial-use constraints. Each observation freezes
the policy and its deadline, so later renewal does not extend old data.

A fetch contains `source`, positive `film_id` (TMDB work), `country`, timezone-aware
`checked_at`, `status` (`complete`, `partial`, `unknown`), optional exact
`plan_scope`, boolean `work_reviewed`, and `assertions`. Assertions use C4's
existing `Assertion`/`Opportunity` fields, preserving source, URL, exact service,
tier/add-on, quality/cut, price/currency, entitlement, work uncertainty and
provider-asserted addition/expiry separately. Missing facts remain null. A
request error is an `unknown` fetch, never a complete empty catalog result.

Only complete reviewed work with an explicit plan scope updates the comparison
baseline. Partial, unknown, unknown-plan and unresolved-work observations remain
inspectable attempts and cannot create disappearance. Events mean
`source_first_seen` or `source_absent` within that one source/work/country/plan;
they do not prove global availability or a provider's release date. Identical
replays create no new observations/events. Conflicting complete payloads at the
same timestamp require review; time cannot move backwards. Writes of the
observation, baseline and events commit together, so interruption can be retried.
`state` distinguishes latest attempt, complete baseline, retained first-seen
checks and provider assertions. First-seen dates cover retained history only;
purge deliberately prevents reconstructing older licensed observations.

`current_opportunities(db, now)` deduplicates current actual opportunities while
retaining each source's assertions. These objects can feed C4 purchase checks
and the existing viewing planner; they never imply account-plan confirmation.
Readers hide denied, expired or terminated policies immediately, and hide each
expired observation even after a source-policy renewal. Physical deletion is
explicit and source scoped:

```sh
uv run python -m film_iq.availability.store_command purge --database private.db --source EXACT_SOURCE --now 2026-10-31T12:00:00Z
uv run python -m film_iq.availability.store_command purge --database private.db --source EXACT_SOURCE --now 2026-10-31T12:00:00Z --execute
```

The first command previews exact observation IDs. Execution deletes expired rows,
or all that source's rows when its policy is denied, expired or terminated;
foreign keys remove corresponding baselines/events. A transition event depends
on both compared observations: its reader checks both deadlines, and deleting
either input cascades the event without deleting the other observation. A
non-content source/time watermark survives purge and rejects historical imports
at or before the purged check time; reacquisition requires a genuinely new
check. It retains no film, service, plan, URL or assertion payload. Editorial evidence and
Movary data are untouched. Existing private backups may contain older cached
provider data: their retention must obey the same approved terms. This command
does not discover or silently modify external backups.

Migration 010 adds only offer-policy/observation/baseline/event tables and the
non-content purge watermark. Existing
editorial revisions and acquisition attempts remain unchanged. Older binaries
refuse schema 10; restore an appropriate private backup to roll back. The usual
online SQLite backup and offline restore preserve this ledger with its foreign
keys and recorded policies. No production provider or polling job is enabled.
