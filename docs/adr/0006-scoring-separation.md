# ADR 0006 — Separate significance, fit and uncertainty

**Date:** 2026-10-29  
**Status:** Accepted separation; provisional weights

## Context
Critic endorsements, Metascore, RT positive share, audience votes and personal taste measure different things.

## Decision
Publish critical evidence and personal preference as distinct components. Separate extraction, identity, evidence/disagreement and prediction uncertainties. Compare simple endorsement/rank-aware/award/aggregate baselines; do not assert the 45/30/15/10 illustrative blend is optimal.

## Consequences
Explainable rankings and retained exploration for sparse/unfamiliar films.

## Validation / reconsideration
Gate: source-family/period holdouts, calibration, preference baselines and robustness; no validation on source-derived TSPDT alone.

## Epic B evidence and recommendation — 2026-10-30

[B7's ten-film 2008 pilot and twelve-film 2023–2024 extension](../research/scoring/study.md)
execute source-family and period/format comparisons. The former retains 61
observed selections; the latter has nine independently audited original-source
critic/film selections across five works. New Yorker is held out by family.
Sparse overlaps, tied training counts, four shorts with unknown exposure and
missing numeric audience inputs leave predictive benefit and weights
inconclusive. These are performed experiments, not calibrated recommendations.

Retain separate transparent component views and derivative-source deduplication.
Do not substitute RT positivity for an average rating, equate categorical
audience grades with votes, impute missing evidence as zero or promote a
weighted blend as optimal. Separation remains accepted; weights remain
provisional, with calibration questions handed to C3 #21.

## Three judgments and a future prediction — 2026-10-30

Display **four distinguishable concepts**, never one opaque `quality`:

1. `personal_enjoyment`: user's own 1–10 judgment of how rewarding/watchable the film was; existing Movary native film rating.
2. `personal_artistic_merit`: user's own 1–10 judgment of artistic achievement; initially explicit `Artistic merit: N/10` viewing-date comment via `user:export:history`, with nullable/review provenance via #58 or user-owned temporary input if the read path is unavailable.
3. `external_critical_recognition`: observed independent original critic/poll/festival/award evidence, with source/edition eligibility, missingness, correct lineage and typed separate count/rank/award/reception components. It is **not** the user's merit score.
4. `predicted_personal_enjoyment` (future): learned estimate, **not** a rating the user supplied; its confidence is not evidence-extraction or identity reliability.

An MVP can report the two human judgments and public evidence without learning any predictions. If personalized modeling is attempted later in C6 #24, evaluate enjoyment against time-ordered held-out actual enjoyment ratings; any use of artistic merit as a second target or combined utility requires an explicit user-selected objective and measured value. Non-ratings are not negative.

**Implementation correction:** `scoring/__init__.py` currently selects the best rank within independence groups, which differs from B7's predeclared representative-source rule; fix in C3 #21 and version the affected score snapshot. No support exists for the illustrative 45/30/15/10 blend, population calibration, or stable shorts/format coverage.

**Evidence:** [B7 study](../research/scoring/study.md), [period/format extension](../research/scoring/holdout-2024/README.md), [Movary tracking semantics](https://docs.movary.org/user-guide/tracking-movies/).
