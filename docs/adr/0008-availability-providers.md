# ADR 0008 — TMDB baseline; specialty provider gate

**Date:** 2026-10-29  
**Status:** Provisional—exploration gate

## Context
A service-level listing is not proof of access, and niche films may be poorly covered. Movie of the Night documents offer classes, links and change events on a free plan.

## Decision
Start with TMDB/JustWatch, with correct attribution. Benchmark 60 stratified films over three dates against Movie of the Night and targeted alternatives. Distinguish add-on, rent, free and subscription; record plan-tier entitlement separately. Do not infer removals from failed requests.

## Consequences
May need two providers or targeted first-party verification; terms/retention and quotas constrain history.

## Validation / reconsideration
Gate: measured coverage, false classifications, timeliness, account entitlement, quota and legally retainable observations.

## POC evidence — 2026-10-30

Direct TMDB metadata/credits and US watch-provider requests supported one real
report for Bicycle Thieves (5156). The selected scenario used an advertised Tubi
`ads` offer with zero incremental purchase cost and explicit unconfirmed
entitlement/playback. JustWatch attribution and the returned provider-information
link are retained. [The live POC](../a7-live-validation.md) establishes this narrow
baseline integration, not provider coverage, commercial retention rights,
first-party playback or plan-tier verification. The 60-film/three-date benchmark
and this ADR's provisional status remain unchanged.

## Epic B paired evidence and discovery scope — 2026-10-30

The [paired date-one report](../research/availability/comparison-20261030.md)
records sixty TMDB and sixty native Movie of the Night HTTP-200 requests.
Usable US responses number 53 and 49; missing-country responses stay unknown.
Asymmetric partial service mapping prevents superiority/absence claims. Public
Apple SKU metadata agrees with three native prices; exact-cut/runtime and
plan-specific uncertainties are retained. A separate native Peacock query
returns twenty first-page movies with more pages available.

Native API fields support discovery before subscription. Consumer login is not
a prerequisite; public title/plan pages are bounded accuracy/qualification
checks and personal entitlement stays unknown where untested. Keep the baseline
and native comparison candidate provisional: all observations are one UTC date,
so two later captures, change/expiry comparisons and unresolved rights/plan
questions remain. No exclusive provider or polling cadence is selected, and
this appendix does not waive the three-date gate.
