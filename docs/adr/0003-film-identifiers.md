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

## Work versus release/cut identity — 2026-10-30

TMDB remains the **operational work crosswalk**, not proof that a distributor offer corresponds to an exact cut, runtime, premiere date, edition eligibility or restoration. Store the original source's title/aliases, person and date contexts unchanged; explicitly label conflicting year/runtime/format/cut assertions as unresolved. A reviewed work match may be accepted while exact-cut/eligibility evidence remains unknown.

Do not force a catalog-absence conclusion after an empty alias search or a budget-limited search. For the small manually curated MVP cohort (#59), a human-reviewed TMDB ID may be supplied; unresolved titles stay in evidence but cannot silently become a watchlist write or verified offer.

**Evidence:** [B2 historical identities and 12/14 bounded automated audit](../research/history/live-20261030.md), [14-case unblinded agent review](../research/history/review-effort-20261030.md), [B4 paired work/cut conflicts](../research/availability/comparison-20261030.md). Auto-match precision and human throughput remain unmeasured.
