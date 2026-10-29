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

