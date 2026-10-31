# ADR 0009 — Explicit monthly bundle utility and budget

**Date:** 2026-10-29  
**Status:** Accepted policy; utility calibrated later

## Context
An individual film ranking does not specify whether one exceptional film is worth several good ones; catalog overlap and current access matter.

## Decision
Compare feasible bundles using current access union candidate access, 5–8 films or hours, runtime and credible departure dates; publish cost assumptions. Compare no purchase and rentals. Never auto-subscribe, cancel or guess pricing/entitlement.

## Consequences
Planner is auditable but utility trade-offs are a user policy, not a mathematical truth.

## Validation / reconsideration
Gate: choose a transparent heuristic and sensitivity-test alternative utility mappings against actual decisions.


## User decision — optional invocation (2026-10-31)

A personal viewing plan, budget, time allowance and utility preference are optional
inputs supplied only when the user chooses to invoke planning. Core discovery,
reports, deployment and release work without them. Test the planner's constraint
and uncertainty contract with declared fixtures; do not ask the user to disclose
private habits or accept a real spending plan to finish development. No inferred
budget/schedule, automatic purchase or default charge follows from the baseline.
The existing declared utility sensitivity is not a learned preference or optimality
claim; provider rights and verified offer qualification remain separate gates.
