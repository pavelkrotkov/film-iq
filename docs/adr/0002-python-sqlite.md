# ADR 0002 — Python modular monolith with SQLite

**Date:** 2026-10-29  
**Status:** Accepted

## Context
Single-user scheduled ingestion and relational evidence do not justify distributed infrastructure.

## Decision
Use Python 3.12+ and one local SQLite DB with migrations, foreign keys, WAL and a scheduled writer. Back up to NAS, not live WAL over a network share. Require SQLite containing the documented WAL-reset fix (3.51.3 or corrected backports).

## Consequences
Small operational surface and testable queries; system and storage restore tests required.

## Validation / reconsideration
Scale away only after measured contention, query or operational limitations.

## Post-POC recovery scope — 2026-10-30

Keep the modular monolith and local SQLite. C1 #19 must separately record fetch **attempts** and accepted semantic revisions; the current `ingest/persist.py` derives a run ID from a revision, so its success/idempotence checks do not prove a durable history of later failed fetch attempts.

For an ongoing deployment, C8 #26 must verify local online backup, WAL-safe restore, compatible migration, integrity/foreign-key checks, active accepted evidence replay and (under specific authorization) a complete Movary database/storage/config/application-version restore. Exercise a failed job/process restart and rights-cache expiry before claiming reliability. Neither microservices, job brokers nor dlt follow from the first-phase measurements.

**Evidence:** [current ingestion](../../src/film_iq/ingest/persist.py), [versioned schema](../../src/film_iq/storage/001.sql) and [bounded SQLite/dlt replay](../research/extraction/README.md).
