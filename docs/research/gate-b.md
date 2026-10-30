# Gate B — working evidence matrix

**Status:** In progress, not a gate decision. Updated 2026-10-30.

**Scope:** [Epic B](https://github.com/pavelkrotkov/film-iq/issues/2) and [issue #18](https://github.com/pavelkrotkov/film-iq/issues/18); [plan](../../plan.md#epic-b--explore-source-universe-and-provider-quality); ADRs [0005](../adr/0005-extraction-choice.md), [0006](../adr/0006-scoring-separation.md), [0008](../adr/0008-availability-providers.md) and [0012](../adr/0012-empirical-gates.md).

The table is a working index, not evidence that any issue is complete. Link each report and record its actual sample, errors, labor, costs, rights and unresolved questions as its evidence is reviewed. Gate B requires the relevant B1–B7 evidence or explicit inconclusive outcomes; do not change provisional decisions on preliminary leads alone.

| Issue | Decision or evidence needed | Current status |
|---|---|---|
| [B1](https://github.com/pavelkrotkov/film-iq/issues/11) | Source priorities, eligibility, independence and rights | [Registry](https://github.com/pavelkrotkov/film-iq/pull/36): 11 source entries; source permissions and some eligibility remain unresolved. |
| [B2](https://github.com/pavelkrotkov/film-iq/issues/12) | Historical and specialty-title identity coverage | [Runnable lookup study](https://github.com/pavelkrotkov/film-iq/pull/39): 14 machine-readable cases and opt-in paginated TMDB search; dry run processes 14 with zero requests. Cached/derivative leads remain unresolved. Failure, incomplete pagination and request limits preserve unknown status; no live coverage, accepted matches or precision estimate. |
| [B3](https://github.com/pavelkrotkov/film-iq/issues/13) | Audited extraction cohort, held-out methods and recovery | [Benchmark](https://github.com/pavelkrotkov/film-iq/pull/40): 32 static derivative sections, 539 independently automated-audited expected records. Frozen baseline complete on 23/24 development and 3/8 held-out documents. Grounded-LLM failed completeness despite 12 valid spans (11 scoped memberships). Real-source edition replay preserved ten rows on source failure and retried to 21 after reopening persistent state. Historical government PDF matched 36/36 first-page rows; original CNC CSV matched 25/25 bounded administrative records. Dynamic query interface and native JSON API agreed on two rows. Separate NFB acquisition failed DNS. No retroactive held-out, film-match, process-crash or broad method-quality claim. |
| [B4](https://github.com/pavelkrotkov/film-iq/issues/14) | Provider coverage, offer correctness, rights, cost and change timeliness | [Runnable experiment](https://github.com/pavelkrotkov/film-iq/pull/41): published work metadata/context checked for all 60 candidates, preserving year/duration/country distinctions. Provider-catalog identities remain unverified and activation fields null. Opt-in observer has credential/retention gates, quota/status evidence and offline failure checks; dry run makes zero requests. Live catalog confirmation, credentials, three-date comparison and account entitlement remain pending. |
| [B5](https://github.com/pavelkrotkov/film-iq/issues/15) | Authorized long-tail leads and library eligibility | [Bounded access research](https://github.com/pavelkrotkov/film-iq/pull/37): six investigations and explicit acceptance accounting; manual checks recommended, no adapter justified. One player request returned HTTP 401. Outcome is inconclusive for US playback and individual entitlement. |
| [B6](https://github.com/pavelkrotkov/film-iq/issues/16) | Reuse candidates, licenses and maintenance cost | [Reuse dossier](https://github.com/pavelkrotkov/film-iq/pull/38): pinned module and license inspection; no measured adoption cost. |
| [B7](https://github.com/pavelkrotkov/film-iq/issues/17) | Public-score baselines, independent holdouts and sparse-film behavior | [Scoring study](https://github.com/pavelkrotkov/film-iq/pull/42): ten-film cohort, 61 selections across three pages, seven unknown list observations. Reception/context transcriptions audited for all ten; separate count/rank/award/reception baselines and tie groups. Full weighted formula remains unknown without numeric audience evidence; renormalized ablations cover only three list-observed films. Retrospective/mixed dates, unknown critic dependence and sparse format/country coverage prevent broad validation. |

## Preliminary constraints

- [Film Comment's terms](https://www.filmcomment.com/terms-of-service/) restrict specified automated collection and reuse. Permission to access a page is not a grant to retain or redistribute its contents.
- [TMDB's movie-provider documentation](https://developer.themoviedb.org/reference/movie-watch-providers) requires JustWatch attribution and does not provide full provider deep links. A service listing is not a verified account entitlement.
- [Watchmode's current terms](https://api.watchmode.com/tc) limit free-plan non-image caching to 30 days and require deletion when the account ends. Apply the actual provider and plan terms before retaining observations.
- [Letterboxd's API policy](https://letterboxd.com/api-beta/) currently excludes several categories relevant to this project, including personal and recommendation projects. An open-source scraper license does not supply source-data permissions.

## Consolidated measurements and unknown costs

These are bounded experiment measurements, not a total cost or quality estimate
for Epic B. Source discovery, agent work, repeat runs and browser asset requests
were not comprehensively metered. Automated audit is not human review labor.

| Evidence | Recorded measurements | Labor, quota and cost limits |
| --- | --- | --- |
| B1 source registry / B6 reuse | Eleven registry entries and a pinned module/license dossier; unresolved rights lead to no-copy decisions. | Source discovery and adoption labor/cost were not timed; qualitative maintenance assessments are not integration benchmarks. |
| B2 identity search | Fourteen dry-run cases, zero provider requests; bounded pagination budget defaults to five pages per query. | No live quota consumption, coverage or precision measurement. Monetary cost and human adjudication minutes remain unknown. |
| B3 static cohort | 97 retained HTTP 200 responses, 359,741 bytes; capture interval 03:06:16–03:07:56 UTC includes pacing. Baseline parsing: 0.0453 s development, 0.0206 s holdout; complete documents 23/24 and 3/8. Current B3 code footprint across experiments: 692 logical Python lines including tests. | Discovery/repeat requests were not fully metered; no independently measured total labor or human correction time. CC BY-SA source text/audits require attribution and share-alike; derivative facts are not independent critical votes. |
| B3 grounded extraction | One blinded agent output, 12 valid spans, 11 scoped memberships; completeness failed. | Full elapsed extraction time, tokens, billing and repeatability unavailable. A valid span does not establish category membership. |
| B3 loader replay / PDF | Replay: ten initial plus eleven new records, source failure/reopen/retry to 21, zero unchanged SQLite writes; one run 0.005 s SQLite and 1.454 s dlt. Separate PDF first page: 36/36 exact rows; native extraction 0.305462 s, saved-text check 0.000943 s. | Installation is outside the timers. SQLite imports precede its timer; the dlt timer can include lazy imports. Historical warm-up state is unknown, so these are not controlled startup or steady-state comparisons. Neither experiment measures production throughput, killed-process recovery or maintenance effort. PDF snapshot validation is not a second extraction engine. |
| B3 dynamic interface | Two bounded HTTP 200 requests: 17,940-byte HTML and 601-byte JSON. Browser and JSON agreed on two IDs/labels; UI reported 1,336 ms. | Browser/model/asset costs unmetered; sequential HTTP timings and UI service time have different boundaries and caches. CC0 output is a defined query, not an original critic list. |
| B3 native CSV | Original CNC resource HTTP 200: 12,821,667 bytes in 39.72 s. First 25 logical records retained as a 3,522-byte native window; 25/25 exact audited observations and omitted-record rejection. One local subset check: 0.001307 s. | Acquisition is outside the subset timer; no full 95,764-record accuracy, held-out-layout or film-identity claim. Declared Licence Ouverte 2.0 with source attribution; raw Date semantics remain unverified. Human correction and total labor unmeasured. |
| B4 offers | Sixty published-work source audits, 64 checked raw/metadata receipt references; provider dry run makes zero requests. | No live provider quota, plan retention, monetary cost, current catalog-ID acceptance or three-date changes measured. Some receipt references share a source response; 64 is not an HTTP request count. |
| B5 access | Six bounded work investigations; two named anonymous metadata probes returned 200 and the player probe returned 401. | Broader discovery requests and labor not fully counted; no playback/account entitlement or comparative coverage result. |
| B7 scoring | Ten-film cohort with 61 critic selections from three pages and two known held-out selections. Reception fields/counts audited for all ten, nine RT means, four categorical audience grades; three-film ablations, zero complete full-weight vectors. Reception acquisition: 20 successful requests with 14.344 s summed request/body-read time; seven later raw-byte captures separately verified. | Request timing excludes pacing/transcription/audit/later captures; not a total study budget. Seven unknown list observations are not negative relevance judgments. No audience sample sizes or numeric vote score; mixed dates and unknown critic overlap prevent temporal or independent reception-validation claims. Labor/billing unmeasured. |

Unknown costs remain explicit insufficient-evidence outcomes for this report.
They must not become a zero-cost assumption or a completed empirical gate.

## Decision record

These are bounded research recommendations, not acceptance of Gate B or changes to production contracts. Cross-cutting ADR decisions remain provisional.

| Component | Outcome supported by current evidence | Remaining evidence |
| --- | --- | --- |
| Source priorities | Prioritize permitted, edition-bounded factual selections and preserve original source families. Restricted criticism/ballots need an appropriate reuse basis before fixture acquisition. Wikipedia copies remain derivative evidence. | Audited original-source eligibility and broader geography/format coverage. |
| Deterministic HTTP extraction | Retain the small HTTP/parser baseline for source-specific experiments, with exact completeness checks and review on failure. The measured 3/8 held-out complete-document rate does not support general unattended extraction. | Additional original publishers and source formats; correction labor. |
| Browser rendering | Static corpus needs no browser. A separate real JavaScript query interface rendered two film rows absent from initial HTML, while its native HTTP JSON API supplied the same rows. Prefer that API for this bounded case. | Original-publisher browser-only inputs, broader layout coverage and any framework benefit. |
| Grounded LLM | No production adoption from the one-case comparison. Valid spans did not prevent an out-of-scope selection or a failed complete-document result. | Independently audited multi-case evaluation, costs and correction effort. |
| SQLite versus dlt | Keep transactional SQLite as the experiment baseline. The edition replay demonstrates retry and persistent-state reopening for both; it does not establish enough incremental benefit to add dlt to production. | Representative job sizes, maintenance/labor costs and process-crash recovery. |
| Availability providers | Insufficient comparative evidence to replace the provisional baseline. Runners and cohorts are preparation, not coverage or entitlement measurements. | Audited IDs, authorized credentials/retention, three observation dates and first-party account checks. |
| Public scoring | Keep weights illustrative. Real observed count/rank disagreement with a tiny held-out sample does not validate a calibrated score or discovery benefit. | Wider independent source/period holds, reception measures, sparse-film and geography/format stability. |

Next work is to complete the prepared identity/provider experiments when their external inputs are available, measure the missing extraction formats and correction effort, and expand the scoring cohort without turning missing selections into negative judgments. No new paid service, crawler platform or production dependency is justified by the current results alone.

## Tracked implementation handoff

The following are proposed deltas to existing Epic C work, linked to the B
evidence that should gate them. They do not change tracker state, finalize ADRs,
require Epic A completion or authorize implementation before its specific gate.

| Existing work item | Evidence and proposed next step |
| --- | --- |
| [C1 #19 — acquisition and revision ledger](https://github.com/pavelkrotkov/film-iq/issues/19) | Consume B3 capture/hash/revision and retry evidence; retain explicit completeness and failure states. Keep a larger job framework gated on measured incremental benefit. |
| [C2 #20 — historical backfill](https://github.com/pavelkrotkov/film-iq/issues/20) | Use B1/B2 source taxonomy and ambiguity cases. Obtain the missing original-source/partial-ballot/layout fixtures and adjudicate catalog candidates before scaling; do not promote the 3/8 held-out complete-document result into automatic acceptance. |
| [C3 #21 — public scoring](https://github.com/pavelkrotkov/film-iq/issues/21) | Keep B7's retrospective two-film comparison as a diagnostic pilot. Expand independent source/period and geography/format holds before selecting calibrated weights or claiming discovery quality. |
| [C4 #22 — offers and entitlement](https://github.com/pavelkrotkov/film-iq/issues/22) | Consume B4's 60 work audits and runners; confirm provider IDs, plan-specific retention, three dated observations and first-party account access before a provider choice. B5 supports bounded manual long-tail checks. |
| [C5 #23 — bundle planner](https://github.com/pavelkrotkov/film-iq/issues/23) | Do not turn unverified entitlements or unknown expiry into purchasable coverage or an optimal plan. Await the relevant B4/C4 evidence rather than the whole of Epic B. |
| [C8 #26 — operations and rights](https://github.com/pavelkrotkov/film-iq/issues/26) | Apply B1/B6 licensing/no-copy decisions and verified provider retention. Instrument remaining acquisition, correction and model costs before operational budget or maintenance conclusions. |

Current insufficient-evidence outcomes remain explicit proposals for gate
review. The unresolved B work stays tracked under #12–#14 and #17–#18; this
handoff does not silently defer or close those issues.
