# ADR 0001 — Movary owns personal state

**Date:** 2026-10-29  
**Status:** Accepted

## Context
Movary already tracks watches, dates, ratings and an intentional watchlist.

## Decision
Keep Movary as authoritative. film-iq reads authenticated API state; writes only approved watchlist additions via API. Its radar/priority states are not a competing watchlist.

## Consequences
No second ratings editor, no direct Movary database edits, no silent deletion or mass promotion.

## Validation / reconsideration
Reconsider only if a documented core Movary limitation persists after a working companion POC.

