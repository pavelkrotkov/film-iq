# ADR 0003 — TMDB crosswalk; keep unresolved evidence

**Date:** 2026-10-29  
**Status:** Accepted

## Context
TMDB, IMDb and Movary IDs are different; obscure/translated works may be ambiguous.

## Decision
Use TMDB as operational external key, optional IMDb and Movary IDs, persistent raw source titles and reviewable match decisions. Never force matches. Contribute genuinely absent films to community catalogs when eligible.

## Consequences
Review queue and audit trails preserve original information without building an alternate comprehensive movie catalog.

## Validation / reconsideration
Measure unresolved rate and matching errors in representative historical/specialty samples.

