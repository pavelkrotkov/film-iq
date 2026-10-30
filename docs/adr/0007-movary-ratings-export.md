# ADR 0007 — Movary CSV export closes rated-only coverage gap

**Date:** 2026-10-29  
**Status:** Accepted for POC; API enhancement deferred

## Context
Played/watchlist endpoints do not necessarily enumerate films that are rated but never recorded as watched. Movary 0.82.1 ships the user:export:ratings command.

## Decision
Use normal API for watched/watchlist and approved additions; import completed ratings CSV snapshots through the documented self-hosted CLI. Treat snapshots as authoritative replacement reads, not append-only events.

## Consequences
No early fork or upstream API required; local filesystem/export scheduling is part of deployment.

## Validation / reconsideration
Check the installed Movary version and deleted-rating behavior; propose an upstream ratings enumeration API only if integration friction justifies it.

## POC evidence — 2026-10-30

The installed 0.82.1 supported exporter streamed a complete, header-only ratings
CSV through `php://stdout --silent`; the actual atomic `export_ratings` adapter
validated zero ratings and reproduced identical bytes on a second export. Authenticated
played/history/watchlist reads and the approved catalog/watchlist round trip also
passed. Rated-only inclusion and deleted-rating replacement are fixture-backed;
the empty live account does not verify those nonempty cases. No test rating was
created. [Gate A evidence](../a7-live-validation.md) records these limits. The
decision remains accepted for POC; no upstream API enhancement was required.

## Two-score MVP read protocol — 2026-10-30

Retain `user:export:ratings` and a validated, atomic **full replacement** CSV for Movary's movie-level **enjoyment** score, including rated-only films and deletions. Gate A exercised two identical **empty/header-only** real exports; nonempty rated-only, changed and deleted real ratings remain unverified.

**Pinned source verification:** Movary 0.82.1 ships [`user:export:history`](https://github.com/leepeuker/movary/blob/0.82.1/src/Command/UserHistoryExport.php) as a companion CLI command, with a CSV containing `watchedAt` and `comment`. The Ratings CSV has `userRating` and no comments. The normal paginated History API's [DTO](https://github.com/leepeuker/movary/blob/0.82.1/src/HttpController/Api/Dto/HistoryEntryDto.php) contains movie and watched date **but no comment**: use the CLI History CSV, not an API response, for the temporary `Artistic merit: N/10` comment convention. The installed, nonempty CLI execution is still an empirical #58 acceptance test.

The [CSV writer](https://github.com/leepeuker/movary/blob/0.82.1/src/Service/Export/ExportWriter.php) repeats the same date-entry comment for multiple plays on that date. Do not treat those repeated rows as independent user merit statements; collapse identical date-level assertions while preserving distinct dates and genuine conflicts. Keep all free-text comments private and intact; missing, invalid or conflicting tags remain unknown/review. The snapshot of History and Ratings should only replace a previous successful snapshot after both exports fully validate; any failure leaves the previous snapshot intact and marked stale.

Only if the supported nonempty history export proves unusable should #58 offer an explicit user-owned **private** merit CSV; do not read Movary's DB directly. C9 #27 considers a native second score only after observed integration friction.
