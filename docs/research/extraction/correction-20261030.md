# B3 timed correction supplement — 2026-10-30

**Issue:** [#13](https://github.com/pavelkrotkov/film-iq/issues/13).
**Scope:** post-holdout, oracle-assisted repair of all six recorded failures
from the frozen 32-document static benchmark. This is correction work on
previously evaluated data, not a new held-out extraction result.

## Protocol and actual work

The [protocol](corpus/correction-protocol.json) was committed as
`14cb7be` before this session inspected the six source sections and their
independent audits. It pins the original result, selection, audits and parser
freeze by SHA-256. Prior benchmark reports had already revealed the failure
classes; this is explicitly not a blinded correction study.

For each case, the agent started UTC and monotonic timers, inspected the
retained source HTML and table/list context alongside the independent audit,
reviewed the original records, wrote explicit edits, and checked the corrected
full records and order against that unchanged audit. The
[ledger](corpus/correction-results.json) retains before/after metrics,
source revision/hash, source locator, rationale, edits, unresolved context and
raw start/end timestamps. No request, framework, source acquisition or parser
change was needed. The adapted observations retain the corpus's
[CC BY-SA attribution and share-alike terms](corpus/NOTICE.md).

The measured intervals include model inference and tool execution/latency.
They exclude earlier source familiarity, protocol/preparation before the case,
gaps between cases, later report writing and CI. These are **agent-assisted
review/correction wall minutes**, not active human minutes, model inference
seconds alone, estimated engineering effort or a billed model-cost measure.
The monotonic clock was read on the same host across the case's start/end
processes. No human worked on these corrections; human active minutes and
billing remain unmeasured rather than zero.

| Case | Split | Actual correction | Seconds | Minutes | Exact rows after review |
| --- | --- | --- | ---: | ---: | ---: |
| `poll-0` | Development | Insert explicit unranked critics' runner-up, excluding directors-poll/prose mentions | 17.626042202 | 0.2938 | 11/11 |
| `shorts-0` | Holdout | Restore six animated-short award-year/edition groups across 30 rows | 26.248615726 | 0.4375 | 30/30 |
| `shorts-1` | Holdout | Restore six live-action-short groups, including standalone year-header rows | 18.657416540 | 0.3110 | 30/30 |
| `shorts-2` | Holdout | Restore six documentary-short groups, including standalone year-header rows | 9.656490734 | 0.1609 | 30/30 |
| `shorts-3` | Holdout | Restore six documentary-feature groups; frozen stratum name is not film format | 9.354713119 | 0.1559 | 30/30 |
| `locarno-2` | Holdout | Select displayed English title instead of italic original-title alias | 15.801860833 | 0.2634 | 20/20 |
| **Total** | Six reviewed failures | **120 category fields, one title field, one inserted row** | **97.345139154** | **1.6224** | **151/151** |

Award-table years remain award labels, not verified release years. Winner
shading and the two explicit tied-winner annotations in `shorts-1` do not
create ordinal selection ranks/ties. Its missing footer note definition remains
reported; the thirty film rows are readable. The locally captured Locarno
heading does not establish parent programme/format context or catalog identity.
The changed alias remains in the ledger's before value. No film match, award
outcome, original publisher truth or additional independent critic vote is
created by these corrections.

## Interpretation and withheld-layout boundary

The untouched first-run benchmark remains **23/24 complete development
and 3/8 complete holdout documents**, with **539 expected observations**.
Of the six failures, the original output had 150 rows against 151 expected and
29 exact full records. Reviewed edits yield 151 exact records and six complete
reviewed documents. Neither the repaired 6/6 nor a combined repaired count is
a new automatic/held-out success rate: the oracle assisted every correction.
Unchanged sources, first-run output, audit and parser hashes are replay-checked.

The original split withheld Academy, Locarno and Annecy publisher groups.
A post-hoc inventory of all 32 captured HTML sections found `th[rowspan]`
year headers only in the four failed Academy holdout cases: six headers per
case, twenty-four total, and none in the twenty-four development captures.
This identifies a concrete withheld layout feature that the frozen baseline
failed. It is a retrospective explanation, not a preregistered layout taxonomy
or proof of all unfamiliar-layout coverage. Other HTML table/list structures
can overlap the splits. Original-publisher browser-only pages, individual
partial ballots and other unusual layouts remain outside this bounded corpus.
The separate original PDF/CSV and dynamic-interface experiments remain
supplements, not relabeled holdouts.

## Footprint, runtime and maintenance decision

The original benchmark's parser runtimes remain 0.0453 s development and
0.0206 s holdout in the recorded single run; the correction minutes have a
separate boundary and cannot be added to acquisition/model billing as a total
study cost. The earlier persistent edition replay remains SQLite 0.005 s and
dlt 1.454 s, with its documented import/warm-up and source-failure boundaries.
It demonstrated persisted reconstruction and retry, not process-kill recovery.

Radon 6.0.1 local module footprints at this supplement's source version:

| Bounded files | Logical Python lines | Maintenance implication |
| --- | ---: | --- |
| `corpus_parser.py`, `corpus_rows.py`, `html_tree.py`, `html_element.py` | 95 | No retuning here; keep the frozen failures and require explicit review of missed membership, year headers and title columns. |
| `sqlite_baseline.py` | 7 | Reuses the existing transaction/upsert facility; this file count excludes database engine and the separate replay harness. |
| `dlt_comparison.py` | 53 | Additional pipeline/state/dependency handling; this count excludes dlt/SQLAlchemy and shared helpers. No measured benefit justifies adoption for this job. |
| `llm_check.py` | 31 | Span and semantic-membership validation remain necessary even when output JSON is valid. No framework benefit was measured. |
| `test_corrections.py` | 32 | Replays sparse edits and verifies pinned original inputs; no production correction subsystem. |

These counts describe named local files, not equivalent complete-system sizes
or lifetime maintenance hours. Billed model cost and human active correction
minutes remain unknown. The measured small correction session supports a
review fallback for these six failures; it does not establish costs on future
sources or justify an LLM/browser framework. Retain deterministic extraction
and transactional SQLite first. Use the documented API for the two-row dynamic
query; keep grounded extraction behind semantic review. Reconsider heavier
components only with measured improvement on an actual remaining workload.

## Reproduce the evidence checks

From the worktree root, with the project environment installed:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
  uv run --no-sync python -m unittest docs.research.extraction.test_corrections
```

These two checks verify frozen-input hashes and replay all six sparse repairs
against the unchanged source-only audit. The existing corpus check still
reproduces the original 26/32 complete-document result. Replaying saved edits
is not a new correction-time measurement.

This supplies a bounded correction-effort observation and clarifies an actual
withheld-layout failure. B3's heavier-tool benefit remains an evidence-based
**no adoption** outcome with unmeasured lifetime/human/billing costs, rather
than an external prerequisite or a claim that every target format is solved.

Validation: Ruff check/format, ty and the full pytest suite passed (**340 passed,
one opt-in integration skipped**); the two correction replay checks run within
the existing research wrapper and also passed directly. Across all 160 Python
files in this branch, maximum CC is 8 and minimum MI is 50.025032. The new
replay module has maximum CC 7 and MI 52.008334. No dependency was added.
