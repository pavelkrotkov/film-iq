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

