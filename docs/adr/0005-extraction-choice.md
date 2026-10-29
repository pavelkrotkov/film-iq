# ADR 0005 — Deterministic first; benchmark additional tools

**Date:** 2026-10-29  
**Status:** Provisional—POC gate

## Context
HTML/RSS/CSV and atypical prose have different extraction costs; adopting Crawl4AI, LangExtract or dlt prematurely increases maintenance.

## Decision
Use API/feeds/HTTP/selector parsing and transactional SQLite first. Benchmark rendered browser, grounded LLM and dlt on 30–40 audited pages and one incremental source. Adopt individual components only if they measurably reduce total cost or error.

## Consequences
No blanket crawler/LLM dependency; difficult one-off pages may be reviewed manually.

## Validation / reconsideration
Gate: held-out correctness/completeness, correction minutes, restart behavior, license and runtime costs.

