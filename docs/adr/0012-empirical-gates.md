# ADR 0012 — POC and exploration precede final dependency choices

**Date:** 2026-10-29  
**Status:** Accepted

## Context
The project is small, and key risks are data quality and decision usefulness, not theoretical concurrency.

## Decision
Create three epics: POC vertical slice, source/provider exploration, and conditional final implementation. Track objective metrics and explicit exit criteria. Add complexity only with concrete failure/likelihood/cost evidence and user approval.

## Consequences
Final implementation can begin at known interfaces while integration of provisional dependencies waits for benchmarks.

## Validation / reconsideration
Gate: publish findings, update the relevant ADR and acceptance criteria before committing an uncertain dependency or architecture.

## Gate A finding — 2026-10-30

[The real source-to-watchlist trace](../a7-live-validation.md) supports acceptance
of the narrow POC after explicit user approval, authoritative API readback and
an idempotent CLI retry with zero further POSTs. The record states its fixture
versus live evidence and unverified quality/rights/operational limits. No new
runtime dependency or uncertain architecture choice was committed. Epic B's
provider/source/calibration work remains independent; production release and
the remaining empirical gates are not accepted by this result.

## Epic B closure interpretation — 2026-10-30

The [Gate B dossier](../research/gate-b.md) distinguishes a performed benchmark
with an inconclusive result from a required experiment not yet performed.
Research need not produce a positive adoption recommendation: insufficient
evidence can support keeping a narrow baseline or rejecting an added dependency.
It cannot supply missing observations.

Epic B's sixty-film/three-date provider benchmark still has only date one. B4,
B8 and the epic remain open until the required later observations and
issue-specific acceptance are recorded, or an explicit scope change is accepted.
No Epic A closure or consumer subscription is a prerequisite. This clarification
preserves the accepted decision and does not accept Gate B.
