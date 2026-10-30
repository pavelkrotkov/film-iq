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

## Feasible-plan contract amendment — 2026-10-30

Implement a versioned, **user-declared** decision utility. Report the **no-new-purchase baseline**, available existing subscriptions, rentals, one new subscription and **one new subscription plus rentals** when relevant; the current POC planner does not evaluate the last hybrid. Compare incremental benefit over access already owned, deduplicating actual films across providers.

Separate **verified feasible access** from **tentative offers** whose plan-specific entitlement, price or cut is unknown. Do not present an unconfirmed subscription, ad tier, library card, add-on or unknown-cost offer as guaranteed watchable at a known price. Expiry applies only where a credible source supplies a date; `first_seen` is not an expiry or launch date. Missing access stays unknown.

Personal enjoyment, personal artistic merit and independent recognition are **separate inputs**; their relative weight (or choosing exceptional over multiple enjoyable films) is a user policy, not learned or proven from the single-film POC. First-use reporting can display feasible/no-purchase alternatives without claiming global optimality. Never auto-subscribe, cancel or buy.

**Evidence:** [POC planner](../../src/film_iq/planning/monthly.py), [planning search](../../src/film_iq/planning/search.py), [A7 tentative Tubi scenario](../a7-live-validation.md); C5 #23 implements the missing cases.
