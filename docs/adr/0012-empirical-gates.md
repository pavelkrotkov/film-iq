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

## Component-specific execution and accepted MVP priority — 2026-10-30

The user chose a **small working personal discovery companion first**, not a broad original-publisher extraction program. **Start gates are component-specific**, not `Epic B complete → every C issue starts`:

- Gate A is **accepted narrowly** (real Movary reads, a header-only export, one approved watchlist addition and safe retry). Begin #58 real personal-state/two-score sync, #59 rights-appropriate curated input and C7 #25 populated read-only report now, alongside scoped C1/C3/C5/C8 correctness/recovery work.
- B1/B2/B3/B5/B6/B7 are completed as **bounded research**, including performed but inconclusive holdouts and explicitly unmeasured human effort. They do not establish unattended extraction, population matching precision, score calibration, actual provider entitlement or source permission.
- B4 #14 **has not completed** three genuinely time-separated dates; registered October 31/November 1 jobs are plans, not observations. B8 #18 and Epic B #2 remain open until those results or an explicitly approved formal gate revision. Production provider/cadence adoption in C4 #22 waits for the reviewed decision; do not alter or trigger the existing jobs as part of the MVP work.
- C2 bulk ingestion waits for source-specific permission, validation and review throughput. C6 modeling and C9 upstream Movary additions are conditional; no unmeasured dependencies are mandated.

Each completed issue or accepted inconclusive experiment must state **performed test**, sample/denominator, rights, what it proves and what remains unknown. No speculative complexity or hidden gate expansion. The initial MVP is a product checkpoint, **not** an automatic Gate B or production Gate C pass.

**Evidence:** [Gate A](../a7-live-validation.md), [Gate B dossier](../research/gate-b.md), [B4 dated protocol](../research/availability/dated-observations.md); current issues #3/#14/#18/#58/#59.
