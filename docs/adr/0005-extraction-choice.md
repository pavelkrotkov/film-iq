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

## Epic B evidence and recommendation — 2026-10-30

The [B3 benchmark](../research/extraction/README.md) independently audits 32
static derivative sections (24 development/eight held out, 539 expected rows).
The frozen parser is complete on 23/24 and 3/8 documents respectively; a valid
LLM span does not establish category membership or complete extraction. The
PDF/CSV and native-API supplements are bounded cases, not new held-out wins.
The incremental replay supports idempotent SQLite and successful retry after a
source failure/reopen, not killed-process recovery or production throughput.

Keep the current HTTP/source-specific parser and transactional SQLite baseline;
use a native API before rendering where it supplies the required records. No
general crawler, grounded-extraction framework or dlt adoption is justified by
these measurements. The [separate correction supplement](../research/extraction/correction-20261030.md)
reviews all six failed documents in 97.345139154 seconds of agent-assisted wall
time, including inference/tool latency, with 151/151 records correct against
the unchanged audit after repair. That is oracle-assisted correction, not a
new automatic holdout rate or active human minutes. Original runtime timings
retain their documented import/warm-up limitations. This is a scoped
recommendation: the provisional status and validation gate are unchanged.
