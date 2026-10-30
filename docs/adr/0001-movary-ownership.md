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

## Revised interpretation — 2026-10-30 (accepted product scope)

The user requires two **independent personal** 1–10 dimensions: **personal enjoyment/watchability** and **personal artistic merit**. A source-derived professional/critical-recognition score is a *third, different* dimension; do not call it the user's merit judgment.

Movary remains the preferred **entry UI and authoritative record** for watched dates, its native film-level personal rating (assigned to **enjoyment**), the watchlist, and user-entered viewing-date comments. Film-IQ may parse an explicit `Artistic merit: N/10` token in a Movary viewing comment into a nullable, traceable **derived snapshot** of the second personal score, via the pinned 0.82.1 `user:export:history` CLI after actual nonempty readback. A Movary comment belongs to a viewing-date entry, not a native second film-level score; conflicting repeat-play tags require review, not silent choice.

If the installed version does not allow a reliable nonempty comment export/read, the MVP may accept a clearly labeled **user-owned, private, local artistic-merit CSV** as a temporary exception, not a duplicate ratings editor or a silent write back to Movary. Preserve provenance and a migration path to Movary. Confirm any upstream second-rating proposal through C9 #27 only after observing actual friction (#58); no fork required by default.

**Evidence:** [live one-film Movary integration](../a7-live-validation.md); [Movary published CSV columns](https://docs.movary.org/user-guide/personal-data/). The two-score user requirement is accepted; automated comment import and nonempty rated-only data remain **untested** until #58.
