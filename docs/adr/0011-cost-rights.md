# ADR 0011 — No new recurring fees unless justified; respect data rights

**Date:** 2026-10-29  
**Status:** Accepted

## Context
Commercial availability providers, criticism and OSS code have varied license and retention rules.

## Decision
Target zero new monthly software/API fees. Store per-provider access/caching/retention/attribution requirements. Public repo includes original code and rights-cleared fixtures, not licensed data dumps. Follow third-party OSS notice requirements and backup secrets privately.

## Consequences
Select source/provider designs that can enforce retention and purge; no automatic rights to redistribute retrieved content.

## Validation / reconsideration
Gate: terms audit and measured coverage/cost before hosted provider or paid model.

## Enforceable source/provider policy — 2026-10-30

A public source page, an OSS client license, a successful HTTP response, **or a manually transcribed rank** does not by itself authorize systematic publisher acquisition, storage, republishing or unrestricted hyperlinking. For each *specific edition/use*, record permitted access method, factual metadata, link/citation rules, retained raw text rights, retention duration, onward reuse, attribution, deletion request response and allowed AI/model uses. Preserve private user-entered Movary comments/ratings outside Git.

**Provider examples to implement as restrictions, not blanket license grants:**
- The dated public TMDB API terms review records a **six-month cache limit**, deletion on termination and AI-application/commercial conditions requiring use-specific assessment. Do not build an indefinite TMDB offer-history archive on unverified permission.
- Movie of the Night's current native terms permit certain functional storage while restricting competing redistribution, third-party material and using service data to train/evaluate/improve AI models. Published Free tier is 1,000 requests/month, **not proof** of actual account allowance.
- BFI, Film Comment and other original publishers have edition-specific terms, including restrictions on automated extraction/storage or hyperlinks. C0b #59 should use only a rights-appropriate small manually curated factual dataset, not an implicit license to scrape a publisher's archive.
- Copyright/terms rights for external film data are **distinct** from the private user's own scores and from the MIT license on film-iq code.

C8 #26 must test a source/provider-policy-aware expiry/purge path, secure storage, request budget and attribution; unresolved rights are an explicit **no-go for the proposed restricted storage/use**, not an assumed permission or a universal ban on factual personal notes. No new fees/providers without measured value and user approval.

**Evidence:** [original source rights registry](../research/sources/registry.md), [provider rights and quota report](../research/availability/rights-20261030.md), [OSS rights dossier](../research/oss-reuse/README.md).
