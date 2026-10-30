# ADR 0010 — CLI/reports first, Movary primary UI

**Date:** 2026-10-29  
**Status:** Accepted

## Context
Movary already provides accounts, watched pages, ratings and watchlist; another frontend duplicates it.

## Decision
Seed a CLI and concise Markdown/HTML reports. Optional notifications and limited HTTP endpoint only if needed; upstream narrowly reusable Movary integration improvements when proven.

## Consequences
Avoid web-app framework, complex auth and duplicate tracking workflows.

## Validation / reconsideration
Gate: demonstrate missing end-user tasks in POC before UI work.

## First useful release boundary — 2026-10-30

Prioritize **existing Movary film-entry UI** and Film-IQ CLI/Markdown/JSON read-only shortlist. The user should be able to record several real watches and both subjective scores using native Movary rating plus a structured comment convention; C0a #58 verifies the data import and C0b #59 imports a manually curated small original-source film-list CSV. C7 #25 consumes both, excludes watched titles, and displays source reasons, both personal scores, and honestly unknown access information.

Do **not** block this vertical slice on universal critic scraping, a weighted scorer, a secondary rating app, real-time notifications, a graph/vector database, or B4/B8's provider selection. Only introduce a separate web input/editor if a user task cannot be accomplished reliably with Movary's existing UI and exports, and its demonstrated benefit outweighs duplication/maintenance.

**Evidence:** [working POC report](../a7-live-validation.md), [Movary documented features](https://docs.movary.org/user-guide/tracking-movies/); MVP issues #58/#59/#25.
