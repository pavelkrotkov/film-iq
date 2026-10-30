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


The [public terms follow-up](../research/availability/rights-20261030.md#public-browser-follow-up-tmdb-terms-now-readable)
now establishes TMDB's six-month cache cap and deletion on termination. Apply
that bound; do not claim perpetual history rights. Its broader AI-application
and commercial-use conditions require proposed-use assessment, without
conflating coding-agent assistance or deterministic comparison with model
training/evaluation. These findings do not select or reject a feed by themselves.

## Gate B remains explicitly open — 2026-10-30

**Status remains provisional.** The same-date 60+60 paired requests yielded 53/60 usable TMDB US observations and 49/60 native Movie of the Night observations. The 529 TMDB service/type rows and 274 native variant rows are **incomparable units**; just 237/529 TMDB units were nominally cross-mapped. Among jointly complete films, 180 mapped tuples appeared in both, 51 only in TMDB, and 46 only in native: these are assertion differences, not validated errors or exclusive coverage.

Only **October 30 UTC** has been measured. B4 #14 requires two genuinely later dates on the frozen both-ID manifest, change/expiry analysis, applicable terms/rights and scoped first-party plan checks; B8 #18 reviews the decision. No observed change means detection latency remains inconclusive. Do not choose a superior feed, polling interval or persistent offer-history policy in advance. TMDB/JustWatch may continue as a clearly tentative **single-film MVP baseline**, without asserted entitlement; leave provider-neutral adapter contracts/test fixtures independent.

Separate public catalog discovery from actual user/account-specific entitlement. Native Movie of the Night published storage permission is subject to third-party rights, attribution, non-redistribution and no-AI-model-training/evaluation conditions. TMDB's publicly reviewed terms state a six-month cache cap and termination purge plus broader AI/commercial-use conditions to assess for the proposed operation; possession of an API key grants no indefinite history or AI-use exception.

**Evidence:** [B4 paired comparison](../research/availability/comparison-20261030.md), [dated runs](../research/availability/dated-observations.md), [rights audit](../research/availability/rights-20261030.md).
