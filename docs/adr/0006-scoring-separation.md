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

## User decision — 2026-10-31

Both personal dimensions are optional, nullable user inputs. Core development,
deployment and release require neither ratings nor a trained personal model.
Public evidence remains usable without them; missing scores never become zero,
negative preference or an inferred artistic judgment. Any later requested model
needs voluntarily available data and appropriate evaluation, without delaying core
delivery or asking the user to create training/acceptance records.
