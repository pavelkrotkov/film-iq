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


## User decision and current acceptance — 2026-10-31

The complete replacement-read contract includes header-only ratings exports and
null personal scores. Nonempty live rating/edit/deletion demonstrations are
optional observations, never development/deployment/release prerequisites. Real
history reads and deterministic fixture coverage can establish the core read-only
integration while those private values are absent. Existing unknown/conflict,
replacement and failure/staleness semantics remain required. The installed stock
API/CLI and optional explicit merit-token mapping require no upstream change or
fork; revisit only a concrete later interface deficiency, not absent user input.
