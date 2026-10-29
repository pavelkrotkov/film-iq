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

