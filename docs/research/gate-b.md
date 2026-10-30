# Gate B — working evidence matrix

**Status:** In progress, not a gate decision. Updated 2026-10-30.

**Scope:** [Epic B](https://github.com/pavelkrotkov/film-iq/issues/2) and [issue #18](https://github.com/pavelkrotkov/film-iq/issues/18); [plan](../../plan.md#epic-b--explore-source-universe-and-provider-quality); ADRs [0005](../adr/0005-extraction-choice.md), [0006](../adr/0006-scoring-separation.md), [0008](../adr/0008-availability-providers.md) and [0012](../adr/0012-empirical-gates.md).

The table distinguishes completed bounded research from open experiments; completion is recorded only after issue-specific acceptance. All seven source PRs are merged. Link each report and record its actual sample, errors, labor, costs, rights and unresolved questions as its evidence is reviewed. Gate B requires the relevant B1–B7 evidence or explicitly accepted deferrals; an inconclusive result does not waive a required unperformed experiment.

| Issue | Decision or evidence needed | Current status |
|---|---|---|
| [B1](https://github.com/pavelkrotkov/film-iq/issues/11) | Source priorities, eligibility, independence and rights | **Closed, completed bounded research** ([acceptance](https://github.com/pavelkrotkov/film-iq/issues/11#issuecomment-6522320655)). [Merged registry](https://github.com/pavelkrotkov/film-iq/pull/36): 11 source entries; unknown permissions and eligibility are documented audit outcomes, not acquired grants. |
| [B2](https://github.com/pavelkrotkov/film-iq/issues/12) | Historical and specialty-title identity coverage | [Runnable lookup study](https://github.com/pavelkrotkov/film-iq/pull/39): 14 frozen cases now have live paginated TMDB searches and details/credits: 35 benchmark requests (21 search, 14 detail), all HTTP 200. Separate automated evidence review supports 12 identities and leaves two date-conflicted cases ambiguous. Six paired source-alias queries retrieve the reviewed candidate in five cases; one empty alias search remains unknown despite a successful English query. No automatic acceptance, human truth or precision estimate. |
| [B3](https://github.com/pavelkrotkov/film-iq/issues/13) | Audited extraction cohort, held-out methods and recovery | [Benchmark](https://github.com/pavelkrotkov/film-iq/pull/40): 32 static derivative sections, 539 independently automated-audited expected records. Frozen baseline complete on 23/24 development and 3/8 held-out documents. Grounded-LLM failed completeness despite 12 valid spans (11 scoped memberships). Real-source edition replay preserved ten rows on source failure and retried to 21 after reopening persistent state. Historical government PDF matched 36/36 first-page rows; original CNC CSV matched 25/25 bounded administrative records. Dynamic query interface and native JSON API agreed on two rows. Separate NFB acquisition failed DNS. No retroactive held-out, film-match, process-crash or broad method-quality claim. |
| [B4](https://github.com/pavelkrotkov/film-iq/issues/14) | Provider coverage, offer correctness, rights, cost and change timeliness | [Paired date-one findings](availability/comparison-20261030.md): all sixty work lookups separately audited; TMDB 53 complete/seven unknown, native Movie of the Night 49 complete/eleven unknown. Partial mapped comparison across 49 jointly complete works: 180 common nominal tuples, 51 TMDB-only, 46 native-only; mapping asymmetry prevents accuracy/absence claims. Public spot checks, Apple SKU prices and separate Peacock pre-subscription discovery are recorded. Two later dates, timeliness and unresolved retention/plan evidence remain. |
| [B5](https://github.com/pavelkrotkov/film-iq/issues/15) | Authorized long-tail leads and library eligibility | **Closed, completed bounded inconclusive research** ([acceptance](https://github.com/pavelkrotkov/film-iq/issues/15#issuecomment-6522322222)). [Merged access research](https://github.com/pavelkrotkov/film-iq/pull/37): six investigations and explicit acceptance accounting; manual checks recommended, no adapter justified. One player request returned HTTP 401. US playback and individual eligibility remain unknown, as the issue permits where testing is infeasible. |
| [B6](https://github.com/pavelkrotkov/film-iq/issues/16) | Reuse candidates, licenses and maintenance cost | **Closed, completed qualitative research** ([acceptance](https://github.com/pavelkrotkov/film-iq/issues/16#issuecomment-6522323392)). [Merged reuse dossier](https://github.com/pavelkrotkov/film-iq/pull/38): pinned module/license inspection and qualitative adoption comparison; the issue does not require measured integration hours. |
| [B7](https://github.com/pavelkrotkov/film-iq/issues/17) | Public-score baselines, independent holdouts and sparse-film behavior | [2008 pilot](https://github.com/pavelkrotkov/film-iq/pull/42) and [period extension](https://github.com/pavelkrotkov/film-iq/pull/47): the 2008 ten-film pilot retains 61 selections and typed reception/award baselines. A frozen twelve-film 2023–2024 period/format extension now has nine independently automated-audited original-source critic/film selections across five works, including two animated features. New Yorker is held out by family; inclusive/main-only views have three/one conditional overlaps, with tied training counts and no training ordinals. Four shorts remain unknown. Full weighted scoring and predictive/format stability remain inconclusive; no weights are selected. |

## Preliminary constraints

- [Film Comment's terms](https://www.filmcomment.com/terms-of-service/) restrict specified automated collection and reuse. Permission to access a page is not a grant to retain or redistribute its contents.
- [TMDB's movie-provider documentation](https://developer.themoviedb.org/reference/movie-watch-providers) requires JustWatch attribution and does not provide full provider deep links. A service listing is not a verified account entitlement.
- [TMDB's rate-limit documentation](https://developer.themoviedb.org/docs/rate-limiting), checked 2026-10-30, describes an approximate anti-bulk ceiling of 40 requests/second, subject to change; respect HTTP 429. The former 40-per-ten-seconds limit was retired in 2019. This published ceiling does not establish an account/monthly quota, monetary allowance or retention permission; no quota headers were observed in this study.
- [Watchmode's current terms](https://api.watchmode.com/tc) limit free-plan non-image caching to 30 days and require deletion when the account ends. Apply the actual provider and plan terms before retaining observations.
- [Letterboxd's API policy](https://letterboxd.com/api-beta/) currently excludes several categories relevant to this project, including personal and recommendation projects. An open-source scraper license does not supply source-data permissions.

- [The current native Movie of the Night terms audit](availability/rights-20261030.md) distinguishes conditional retained storage, attribution and the specific AI-model-training/evaluation restriction from older repository terms. Its published Free quota is 1,000 requests/month; native API access is now demonstrated by the paired continuation; actual account balance/plan and TMDB historical retention remain unverified.

## Consolidated measurements and unknown costs

These are bounded experiment measurements, not a total cost or quality estimate
for Epic B. Source discovery, agent work, repeat runs and browser asset requests
were not comprehensively metered. Automated audit is not human review labor.

| Evidence | Recorded measurements | Labor, quota and cost limits |
| --- | --- | --- |
| B1 source registry / B6 reuse | Eleven registry entries and a pinned module/license dossier; unresolved rights lead to no-copy decisions. | Source discovery and adoption labor/cost were not timed; qualitative maintenance assessments are not integration benchmarks. |
| B2 identity search | Fourteen primary searches (15 requests, 70 candidate occurrences), fourteen selected detail requests and six alias requests: 35 benchmark requests. All complete/HTTP 200; independent automated audit supports 12 identities, leaves two ambiguous. | No quota headers returned; quota capacity is unknown. Detail requests total 1.2903 s; primary search durations unmeasured. Audit wall interval 103.617 s is automated, not human labor. Automatic-acceptance coverage is zero; precision undefined. Monetary cost and human adjudication minutes remain unknown; the separate authentication probe is outside benchmark totals. |
| B3 static cohort | 97 retained HTTP 200 responses, 359,741 bytes; capture interval 03:06:16–03:07:56 UTC includes pacing. Baseline parsing: 0.0453 s development, 0.0206 s holdout; complete documents 23/24 and 3/8. Current B3 code footprint across experiments: 692 logical Python lines including tests. | Discovery/repeat requests were not fully metered; no independently measured total labor or human correction time. CC BY-SA source text/audits require attribution and share-alike; derivative facts are not independent critical votes. |
| B3 grounded extraction | One blinded agent output, 12 valid spans, 11 scoped memberships; completeness failed. | Full elapsed extraction time, tokens, billing and repeatability unavailable. A valid span does not establish category membership. |
| B3 loader replay / PDF | Replay: ten initial plus eleven new records, source failure/reopen/retry to 21, zero unchanged SQLite writes; one run 0.005 s SQLite and 1.454 s dlt. Separate PDF first page: 36/36 exact rows; native extraction 0.305462 s, saved-text check 0.000943 s. | Installation is outside the timers. SQLite imports precede its timer; the dlt timer can include lazy imports. Historical warm-up state is unknown, so these are not controlled startup or steady-state comparisons. Neither experiment measures production throughput, killed-process recovery or maintenance effort. PDF snapshot validation is not a second extraction engine. |
| B3 dynamic interface | Two bounded HTTP 200 requests: 17,940-byte HTML and 601-byte JSON. Browser and JSON agreed on two IDs/labels; UI reported 1,336 ms. | Browser/model/asset costs unmetered; sequential HTTP timings and UI service time have different boundaries and caches. CC0 output is a defined query, not an original critic list. |
| B3 native CSV | Original CNC resource HTTP 200: 12,821,667 bytes in 39.72 s. First 25 logical records retained as a 3,522-byte native window; 25/25 exact audited observations and omitted-record rejection. One local subset check: 0.001307 s. | Acquisition is outside the subset timer; no full 95,764-record accuracy, held-out-layout or film-identity claim. Declared Licence Ouverte 2.0 with source attribution; raw Date semantics remain unverified. Human correction and total labor unmeasured. |
| B4 offers | Earlier 225 TMDB requests remain separate. New paired pass: 120 HTTP 200 requests, plus one native probe; Peacock supplement adds one native request, totaling 122 new provider requests (60 TMDB/62 native). Apple adds one explicit public HTTP lookup. TMDB 529 source units versus native 274 quality variants; 49 jointly complete films. | Mapping covers 237/529 TMDB units versus 274/274 native variants; 292 TMDB units remain unmapped. Native-only mapped tuples can correspond to unmapped TMDB units. No quota headers; allowance, actual costs and human labor unknown. Capture 12:53:42.210692–12:54:06.199569 UTC; pair start skew 0.149584–0.346159 s. Public pages and SKU metadata do not prove playback or exact tiers; personal entitlement stays unknown without blocking discovery. |
| B5 access | Six bounded work investigations; two named anonymous metadata probes returned 200 and the player probe returned 401. | Broader discovery requests and labor not fully counted; no playback/account entitlement or comparative coverage result. |
| B7 scoring | Ten-film cohort with 61 critic selections from three pages and three held-out selections across two films. Reception fields/counts audited for all ten, nine RT means, four categorical audience grades; three-film ablations, zero complete full-weight vectors. Reception acquisition: 20 successful requests with 14.344 s summed request/body-read time; seven later raw-byte captures separately verified. | Request timing excludes pacing/transcription/audit/later captures; not a total study budget. Seven unknown list observations are not negative relevance judgments. No audience sample sizes or numeric vote score; mixed dates and unknown critic overlap prevent temporal or independent reception-validation claims. Labor/billing unmeasured. |

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
| Availability providers | [Same-date paired observations](availability/comparison-20261030.md) support bounded positive assertions and explicit missing-country unknowns, not provider superiority or exact-tier accuracy. Partial nominal overlap preserves channels, free/ads distinctions and unmapped units. Peacock API/public-plan discovery needs no consumer login. | Reuse the accepted both-ID manifest on two genuinely later dates; resolve TMDB historical-retention basis, measure change timeliness and investigate plan-specific classifications. Personal entitlement stays unknown in pre-subscription discovery; optional account-specific validation is not a prerequisite. |
| Public scoring | Keep weights illustrative. Real observed count/rank disagreement with a tiny held-out sample does not validate a calibrated score or discovery benefit. | Wider independent source/period holds, reception measures, sparse-film and geography/format stability. |

Next work is to complete the prepared identity/provider experiments when their external inputs are available, measure the missing extraction formats and correction effort, and expand the scoring cohort without turning missing selections into negative judgments. No new paid service, crawler platform or production dependency is justified by the current results alone.

The remaining issue-specific experiments are concrete:

| Open issue | Next bounded measurement |
| --- | --- |
| B2 #12 | Time actual manual adjudication/correction by the existing source strata, preserving unresolved decisions and undefined automatic precision; no human-only identity oracle is added as a requirement. |
| B3 #13 | Time correction of observed extraction failures in a separately labeled supplement, preserving the frozen baseline and stating method/model-cost boundaries. Clarify or complete withheld-layout evidence without relabeling development supplements as holdouts. |
| B4 #14 | Reuse the accepted both-ID manifest on two later dates, measure changes/expiry, resolve retention/use questions and investigate public plan-specific classifications. Native access and bounded public spot checks are performed; consumer login is not required for discovery. |
| B7 #17 | Add a frozen period/diversity holdout with independently sourced critic selections, or obtain an explicit scoped deferral. The existing New Yorker source-family holdout is a valid performed experiment; missing numeric audience inputs are a legitimate inconclusive full-formula result. |
| B8 #18 / Epic #2 | Consolidate those outcomes and any explicitly accepted deferrals before a final gate decision; the current synthesis does not close either item. |

## Tracked implementation handoff

The following are proposed deltas to existing Epic C work, linked to the B
evidence that should gate them. They do not change tracker state, finalize ADRs,
require Epic A completion or authorize implementation before its specific gate.

| Existing work item | Evidence and proposed next step |
| --- | --- |
| [C1 #19 — acquisition and revision ledger](https://github.com/pavelkrotkov/film-iq/issues/19) | Consume B3 capture/hash/revision and retry evidence; retain explicit completeness and failure states. Keep a larger job framework gated on measured incremental benefit. |
| [C2 #20 — historical backfill](https://github.com/pavelkrotkov/film-iq/issues/20) | Use B1/B2 source taxonomy and ambiguity cases. Obtain the missing original-source/partial-ballot/layout fixtures and adjudicate catalog candidates before scaling; do not promote the 3/8 held-out complete-document result into automatic acceptance. |
| [C3 #21 — public scoring](https://github.com/pavelkrotkov/film-iq/issues/21) | Keep B7's retrospective two-film comparison as a diagnostic pilot. Expand independent source/period and geography/format holds before selecting calibrated weights or claiming discovery quality. |
| [C4 #22 — offers and entitlement](https://github.com/pavelkrotkov/film-iq/issues/22) | Consume B4 work audits, paired runners and source-specific unknowns; preserve IDs/quality/add-on lineage. Complete three-date comparison, rights and public plan qualifiers before a provider choice. Use public plan rules for prospective subscriptions; personal entitlement remains an optional account-specific check, not a discovery gate. |
| [C5 #23 — bundle planner](https://github.com/pavelkrotkov/film-iq/issues/23) | Do not turn unverified entitlements or unknown expiry into purchasable coverage or an optimal plan. Await the relevant B4/C4 evidence rather than the whole of Epic B. |
| [C8 #26 — operations and rights](https://github.com/pavelkrotkov/film-iq/issues/26) | Apply B1/B6 licensing/no-copy decisions and verified provider retention. Instrument remaining acquisition, correction and model costs before operational budget or maintenance conclusions. |

Current insufficient-evidence outcomes remain explicit proposals for gate
review. The unresolved empirical work stays tracked under #12–#14 and the Gate B
synthesis under #18. The formerly missing #17 period/format experiment is now
executed in PR #47; its acceptance is adjudicated separately against the exact
issue criteria. This handoff does not itself accept Gate B or silently defer work.


## Authenticated continuation — 2026-10-30

The user-supplied project-local TMDB v3 key was accepted by a separate read-only
authentication probe. [B2 PR #39](https://github.com/pavelkrotkov/film-iq/pull/39)
now reports 35 benchmark requests and a fresh
[GPT-6.1 Sol High review](https://github.com/pavelkrotkov/film-iq/pull/39#pullrequestreview-5711278183).
Standards and Spec found no actionable defects; human precision, labor and
confirmed absence remain unmeasured.

For B4, the same 60-film cohort was independently audited against current
TMDB details/directors and source work metadata before a local manifest enabled
provider calls. This accepts a work identifier for offer lookup, not a dated
release event or a cut. B2's more conservative date-conflicted audit statuses
remain separate; neither audit supplies human precision truth. Four broad
searches (Joker, The River, Flow, Tea) exhausted the five-page budget and remain
incomplete even when positive work identity evidence supports the selected ID.

The first US observation gives ten usable responses in each of five assigned
strata and three usable / seven unknown among the shorts/experimental stratum.
Those assigned groups are not a feature/short partition: the older group also
contains a short. All 53 usable responses contain offers; none is a complete
empty-US response. The 529 source-normalized rows comprise 81 subscription,
218 rent, 204 buy, eight ads and eighteen free rows. These are service/film/type
observations, not 529 films, independently verified offers or entitlements.
The seven later diagnostic rechecks lacked an explicit US object; original failed response bodies/hashes were not retained, so those later results do not prove byte-identical original failures. This
is unknown rather than evidence of US unavailability or a removal.

[Netflix's Nimona page](https://www.netflix.com/title/81444554),
[Disney+'s Inside Out 2 page](https://www.disneyplus.com/browse/entity-ec9f9fa3-fbae-4a25-b722-12c3b8ab0ef4)
and [Apple's US No Other Land page](https://tv.apple.com/us/movie/no-other-land/umc.cmc.74yuh67fhbawv4o96mks0y1y2)
provide bounded first-party catalog-presence evidence via a public web reader.
Crawled pages are not live playback/account tests. Generic plan advertisements
do not establish title-specific ad-tier access, and Apple's reader exposed no
rent/buy transaction or price. No purchase-driving entitlement is verified.
This paragraph describes the earlier TMDB-only pass. The [later paired continuation](availability/comparison-20261030.md) now includes native Movie of the Night, public signed-out spot checks and Apple SKU metadata. It is still the same UTC observation date; two later dates remain. No polling cadence or Gate B acceptance follows.


## Executed period and format holdout — 2026-10-30

[PR #47](https://github.com/pavelkrotkov/film-iq/pull/47) executes the previously
missing B7 extension on twelve works frozen before acquisition. Fifteen Wikipedia
requests include two missing-page API errors and one wrong-article response; all
are retained before three ordinary corrections establish the intended twelve
articles. HTTP 200 was not treated as proof of correct work identity.

The Wikipedia-only pass yields one identified critic selection. An explicitly
exploratory original-list backfill was frozen after this sparsity was observed,
without changing films, holdout family or arithmetic. Independent source audits
verify nine distinct critic/film selections from NPR and The New Yorker across
five films; a derivative duplicate adds no critic. Main lists, honorable mentions
and supplementary recommendations retain different categories. One optional
source's unverified rank remains excluded after the independent reader's 403.
No paywall bypass or publisher-body copy was used.

The inclusive view has three supported family overlaps; the main-only view has
one. Training counts tie and all training ranks are unknown, so this is an
executed but inconclusive predictive comparison. Two animated works have positive
selection evidence; all four shorts retain unknown exposure. The country/format
report includes denominators and overlapping country memberships. Wider stability
and discovery benefit are not inferred from these sparse outcomes. The original
2008 results, production scorer and illustrative weights remain unchanged.

This supplies the required bounded period/diversity experiment without requiring
a positive quality result. Manual review/correction metrics for B2/B3, B4's two
later observation dates, change timeliness and unresolved rights/plan-specific
classifications, and final Gate B adjudication remain outstanding. Native access
and bounded public offer checks are now performed; consumer-account checks remain
optional and are not prerequisites for discovery. Automated audit intervals are labeled as such and do not
stand in for human effort.
