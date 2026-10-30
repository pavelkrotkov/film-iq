# ADR 0005 — Deterministic first; benchmark additional tools

**Date:** 2026-10-29  
**Status:** Accepted narrow deterministic default; broader tools remain gated

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
retain their documented import/warm-up limitations. This paragraph records
an earlier **provisional** recommendation; the **narrow deterministic default** was
subsequently accepted in the decision immediately below. General tools and
unattended unfamiliar-layout extraction remain gated.

## Narrow adoption decision — 2026-10-30

**Accepted baseline:** use a documented native API/structured file when available; otherwise source-specific deterministic HTTP extraction plus explicit independent **complete-document, category and rank/tie checks**, transactional SQLite, and a review/abstention path. This does **not** accept unattended processing of unfamiliar layouts. Do not adopt a general browser crawler, LangExtract, dlt or a generalized LLM ingestion pipeline on first-phase evidence alone.

**Measured limits:** B3's frozen 32 Wikipedia derivative sections (539 expected observations) completed **23/24 development** and **3/8 held-out** documents automatically. Six oracle-assisted corrections took **97.345 seconds agent wall time** and produced 151/151 reviewed rows; this was not a new held-out rate or human labor metric. One grounded-LLM check returned an out-of-scope membership despite source grounding. A native JSON API answered a two-row JavaScript-interface query without browser rendering. The persisted 21-observation SQLite/dlt replay did not establish dlt benefit or production crash recovery.

**Reconsider** another extraction tool only for an actual permissioned source whose native/HTTP extraction fails, when an independently audited, unseen layout/format comparison demonstrates meaningfully higher *complete-document* correctness or lower total correction/operating cost without unacceptable rights or dependency burden. Prefer one-off review for a one-off page.

**Evidence:** [B3 corpus/results](../research/extraction/README.md), [timed corrections](../research/extraction/correction-20261030.md). C0b #59 is a curated data import, not a crawler; C2 #20 owns future permitted source expansion.
