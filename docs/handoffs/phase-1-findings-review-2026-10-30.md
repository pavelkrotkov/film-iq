# Phase 1 findings → architecture/roadmap review handoff

**For:** an independent senior architecture, data-quality and product-review agent  
**Project:** [film-iq](https://github.com/pavelkrotkov/film-iq)  
**Snapshot:** 2026-10-30, `main` at [`0dfd494be0e11c419030902f80afd56fa0ced1cd`](https://github.com/pavelkrotkov/film-iq/commit/0dfd494be0e11c419030902f80afd56fa0ced1cd)  
**Status:** review instructions and evidence inventory, **not** an accepted Gate B decision or a replacement for `plan.md`. Subsequent changes must be rechecked against the live repository.

## 1. Your mission

Independently assess the POC (Epic A) and empirical source/provider research (Epic B). Determine which original white-paper/`plan.md` design decisions are **supported, disproven, weakened, or still undecidable**, and how that should alter Epic C implementation priorities and dependencies.

Be rigorous about both sides: do not demand complex infrastructure based on theoretical problems; do not treat green CI, agent audits, or closed GitHub issues as proof of film identity, source extraction, streaming entitlement, predictive accuracy, data rights or user utility. Identify the **smallest additional experiment** that can genuinely resolve each consequential uncertainty.

Your main deliverable is a critical, evidence-linked Markdown **Phase 1 assessment and revised Epic C proposal**. Start **read-only**: examine code, findings, review discussions, issue states, PRs and authoritative source references. **Do not** re-run live data acquisition, edit the Movary account, use or expose saved API tokens, change native collection jobs, adopt providers, update ADR statuses, or alter GitHub issues before reporting proposed changes for approval. You may run credential-free tests and inspect rights-cleared fixtures.

## 2. Project's actual objectives

The proposed product is **not another tracker**. It joins original critics' lists, editorial polls and festival/award evidence with reliable film identities, separate critical significance and personal-fit signals, US legal viewing options and a practical 5–8-films/month (or configured hours) service/rental/no-purchase plan.

Three separate evaluation objectives: (1) representation of critical recognition, (2) prediction of personal satisfaction, (3) feasible viewing/subscription choices. Optimizing one is not proof of the other two. Movary remains authoritative for watched status, personal ratings and intentional watchlist; film-iq owns source evidence, identity decisions, scores, offer observations and plans. Zero-new-recurring-API-fees is a target, not a proved operating budget.

**Primary specification:** [plan.md](../../plan.md), especially `10 and the post-POC/empirical appendices near its end. Read [ADRs](../adr/README.md) before recommending changes, and examine [AGENTS.md](../../AGENTS.md) for development and review discipline. The plan contains **chronological annotations**: newer measured findings supersede some older pending-status sentences; preserve that temporal distinction.

## 3. Verified tracker snapshot

| Epic/issue | Actual GitHub state as checked on Oct 30 | Meaning |
| --- | --- | --- |
| [Epic A #1](https://github.com/pavelkrotkov/film-iq/issues/1), children [#4–#10](https://github.com/pavelkrotkov/film-iq/issues) | **Closed: 7/7 child issues closed**, Gate A accepted | Narrow, functioning POC; **not a production release or quality benchmark** |
| [Epic B #2](https://github.com/pavelkrotkov/film-iq/issues/2) | **Open: 6/8 children closed** | Completed bounded B1/B2/B3/B5/B6/B7; remaining B4/B8 |
| [B4 #14](https://github.com/pavelkrotkov/film-iq/issues/14) | **Open** | Provider comparison requires two additional genuinely later observation dates and adjudication |
| [B8 #18](https://github.com/pavelkrotkov/film-iq/issues/18) | **Open** | Research dossier prepared, but final gate depends on B4 |
| [Epic C #3](https://github.com/pavelkrotkov/film-iq/issues/3), [#19–#27](https://github.com/pavelkrotkov/film-iq/issues) | **Open: 0/9 child issues closed** | Implementation still proposed and conditional; some components may start after their *specific* gate, not only after entire Epic B |

**Tracker nuance:** B1/B2/B3/B5/B6/B7 were closed with findings in comments and committed reports, although their original issue-body acceptance checkboxes remain unchecked. The closure and scope must be verified against reports/PRs rather than inferred solely from checkbox counts.

No open PRs were found at the snapshot. Current `main` had passing GitHub **Python Quality**, **Tests**, and **Security/Workflow Lint** runs on the above SHA. The [consolidated plan](../../plan.md) reports 341 local passed tests and one skipped opt-in live test before the final housekeeping PR; confirm scope and current CI before making a release claim.

### Pending time-based observation, not an agent task

The [dated B4 collection protocol](../research/availability/dated-observations.md) documents two **local macOS launchd jobs**, scheduled:

- **2026-10-31 at 10:00 America/New_York = 14:00 UTC**
- **2026-11-01 at 10:00 America/New_York = 15:00 UTC** (DST transition)

The jobs were registered and guarded against premature execution, with zero completed runs when last inspected. They use the same accepted 60-film **both-ID manifest**, are capped at **120 provider requests per pass**, and use installed Python 3.12 from root `main`. They require Mac/network availability. Registration does **not** establish that the future captures occur; if a job fails, a genuinely later date is required, not another same-day sample. The runner collects observations only: it does **not** analyze changes, adjudicate B4/B8, close issues, or wake an agent.

[PR #56](https://github.com/pavelkrotkov/film-iq/pull/56) documents worktree cleanup: 790 locally preserved SHA-256-verified private evidence files (~26.4 MB) under the ignored `.cache/research-evidence/<worktree-name>/<original-relative-path>` hierarchy; old worktrees removed, branches/commits retained. Treat this as documented local state, **not cloud-accessible GitHub source material**. Never print credentials or publish provider response bodies. Refer to the [protocol](../research/availability/dated-observations.md) and [#14 comments](https://github.com/pavelkrotkov/film-iq/issues/14) for actual execution requirements.

## 4. Epic A: what was demonstrated, and what was not

**Direct evidence:** [A7 live validation](../a7-live-validation.md), [actual API trace](../a7-live-write-result.json), [POC report contract](../poc-report.md), [Epic A closure](https://github.com/pavelkrotkov/film-iq/issues/1), [PR #49](https://github.com/pavelkrotkov/film-iq/pull/49).

- **A real approved API round trip occurred.** An original BFI directors' poll fact for *Bicycle Thieves* (=20, tie preserved) was linked through a manually reviewed match to TMDB **5156**. US TMDB/JustWatch offers were classified. A configured **89-minute / 90-minute** Tubi ads scenario had **$0 incremental purchase cost**, but **entitlement and playback remained unconfirmed**. The user approved the exact watchlist preview, not a broad sync.
- After fixing an actual invalid/missing TMDB application key in the existing Movary 0.82.1 deployment, the CLI requested the movie (HTTP 200), added the Movary catalog movie (HTTP 200), and added the watchlist item (HTTP 204). Authoritative readback showed distinct Movary ID **1** and exactly one watchlist entry for TMDB **5156**. A repeat had **two GETs, zero POSTs**, no duplicate, no deletion. Reported single-run durations **0.459 s** and **0.175 s** are not performance distributions.
- Four rights-cleared captured derivative page sections were audited to **42 observations** with rank/tie/unranked/partial semantics; ingestion and automatic-decision replay demonstrated semantic idempotence and failure/unknown behavior for this corpus.
- Movary's installed `user:export:ratings` and atomic reader were exercised with **two identical empty/header-only** real exports (zero ratings). Nonempty rated-only and deleted-rating cases are **fixture tests**, not live-data evidence. The real account had no played/history items in this check.
- The **four-case held-out identity evaluation automatically accepted zero** matches, leaving precision **undefined**; a separate reviewed POC match was performed. Do not infer any population 99% auto-match precision or claim negligible long-tail metadata problems.
- A1's score and current planner are transparent **baselines**, not empirically calibrated personal ranking or an optimal subscription allocator. End-to-end read-only report behavior is tested; no real playback, satisfaction, consumer entitlement, ongoing monitoring, broad source accuracy or restore has been verified.

**Review questions:** Does the existing schema preserve enough source/edit history? Does an explicit zero-auto-accept identity policy make the first full backfill impractical without a measured review-cost plan? Is the report a user-usable discovery product or only a trace demonstrating the integration boundary? Are watchlist approval, secrets and idempotence appropriate without needless extra infrastructure?

## 5. Epic B: bounded research evidence

Read [Gate B dossier](../research/gate-b.md) first, then the exact source reports below. Distinguish **closed issue**, **performed experiment**, **positive result**, and **production adoption decision**: they are not synonyms.

| Study | Actual findings | Do **not** infer |
| --- | --- | --- |
| [B1 #11 — source registry](../research/sources/registry.md) | **11 audited source entries**, ranking/eligibility/lineage/rights distinctions, including international and specialist sources. BFI, Film Comment and festival/license restrictions documented. | Permission to systematically crawl, retain, republish or deep-link all historical publisher content; complete edition coverage |
| [B2 #12 — historical/identity](../research/history/live-20261030.md), [effort](../research/history/review-effort-20261030.md) | **14 frozen cases**, **35 TMDB benchmark requests**, 12 work identities supported by automated independent review and 2 date-conflicted/ambiguous cases. No automatic accepted matches. Separate unblinded agent review **59.235865 seconds**; zero human active minutes measured. | Population identity precision, real-world human correction throughput, verified absence of obscure catalog films |
| [B3 #13 — extraction](../research/extraction/README.md), [corrections](../research/extraction/correction-20261030.md) | **32 derivative Wikipedia sections**, **539** expected observations. Frozen deterministic parser achieved **23/24 development** and **3/8 held-out** complete documents, despite high title matching. One grounded-LLM extraction included an **out-of-scope** selection even with valid source spans. Agent/oracle-assisted corrections handled all six failures in **97.345 s** and reconciled **151/151** reviewed records *after* the failed first run. Persistent limited replay supported simple SQLite; dlt adds no measured benefit. Separate original PDF/native API/CSV/dynamic supplements are bounded, not new held-out wins. | General autonomous extraction reliability, human labor cost, cross-publisher generalization, LLM groundedness as semantic correctness, dlt necessity |
| [B7 #17 — scoring](../research/scoring/study.md), [period/format holdout](../research/scoring/holdout-2024/README.md) | Ten-film 2008 pilot contains **61** observed selections. A frozen 12-film 2023–24 extension yields **9 independent original-source critic/film selections among 5 films** after sparse derivative evidence; training-family overlaps are tied and four shorts have unknown exposure. Outcome: **performed but inconclusive**. | Optimal 45/30/15/10 weights, out-of-sample personal preference prediction, international/format stability, quality of sparse recommendations |
| [B5 #15 — lawful long-tail](../research/long-tail/README.md) | Six targeted official/library/archive leads, with partial/preview and account restrictions kept distinct. No proven US playback or measured improvement over primary providers. | A generally reliable authorized full-film crawler or a usable library subscription |
| [B6 #16 — OSS reuse](../research/oss-reuse/README.md) | Studied GoodWatch, Cinemagoria, Kometa/letterboxdpy, MDBList, Critics Lists Aggregator and PaperSeek. Found useful *design patterns* and licensing/completeness caveats; no broad stack adoption or code-copy case. | Permission to reuse particular source data or benefit from adding all those dependencies |

### B4 — specifically unfinished, not failed

[First paired native comparison](../research/availability/comparison-20261030.md), [protocol](../research/availability/dated-observations.md), [rights/terms audit](../research/availability/rights-20261030.md), [issue #14](https://github.com/pavelkrotkov/film-iq/issues/14).

- Same date **2026-10-30 UTC**: **60 TMDB/JustWatch + 60 native Movie of the Night requests**, all HTTP 200. **53/60** usable TMDB US responses and **49/60** usable native responses; missing US country remains **unknown**, not empty. Shorts/experimental are the major coverage gap in both. **49 films** have jointly complete observations.
- TMDB returned **529 service/type rows**, native returned **274 offer/quality variants**; these are different units. Only **237/529 TMDB rows** were manually nominally mapped. On jointly complete films the normalized comparison reports **180 common, 51 TMDB-only, 46 native-only mapped tuples**; these are *assertion differences*, not independently verified provider errors, absences or a winner.
- Public first-party Netflix/Disney/Criterion examples and an Apple SKU price lookup support specific bounded presences/prices, **not** tier eligibility, signed-in playback, actual checkout or global accuracy. Several source runtime/year/cut conflicts remain.
- Native Movie of the Night currently advertises a **1,000 requests/month Free plan**, under specific retention/attribution/third-party and no-AI-model-training/evaluation constraints. The actual account allowance, cost and terms acceptance were **not** inspected. The current public TMDB terms review documents a **six-month cache cap**, deletion at termination and other project/use constraints that need application-specific assessment. No unconditional indefinite offer-history right is established.
- **Only one date exists.** Two planned later observations must be completed and compared. If no changes are observed, report a no-change interval and **inconclusive detection latency**, not measured zero latency or confirmed completeness. No consumer service login is required to establish public catalog discovery, but user-specific tier/entitlement is separately unknown.
- ADR [0008](../adr/0008-availability-providers.md) remains **provisional**. Do not pick a superior provider, change polling cadence, or claim an optimal subscription without the required evidence.

## 6. Architecture status before your review

**Currently supported as a narrow baseline:**
- Movary personal-state ownership; read via API, existing complete ratings-export CLI, and approved-only watchlist writes (ADRs [0001](../adr/0001-movary-ownership.md), [0007](../adr/0007-movary-ratings-export.md)).
- Python modular monolith, locally stored SQLite with auditable typed evidence and revisions; no demonstrated need for microservices or graph/vector infrastructure ([0002](../adr/0002-python-sqlite.md), [0004](../adr/0004-typed-provenance.md)).
- Nullable TMDB/IMDb/Movary identity crosswalk, original raw titles and reversible review; no forced speculative match ([0003](../adr/0003-film-identifiers.md)).
- Structured independent-source evidence separated from personal fit, offer entitlement and budget decisions; CLI/report first ([0006](../adr/0006-scoring-separation.md), [0009](../adr/0009-bundle-optimization.md), [0010](../adr/0010-interface-scope.md)).
- Deterministic HTTP/native API and SQLite as the **smallest justified initial tooling**. Prefer completeness-failure/review to silent automatic acceptance.

**Not settled by this phase:** whether additional extractors, dlt, paid providers, LLM enrichment, embeddings, a secondary interface, full account entitlement verification, calibrated weights, or more sophisticated calendar optimization would be worth their complexity. [ADRs 0005, 0006 weights, 0008, 0012](../adr/README.md) preserve appropriate gates. An inconclusive result is a legitimate *outcome* of a performed experiment, but not a substitute for an *unperformed* required date.

**Major product risk to investigate:** the very sparse and copyright-constrained original critical evidence may limit usable global long-tail discovery more than SQLite/API architecture does. Assess whether the proposed evidence/permission strategy and quality-review throughput can actually build the intended catalog at reasonable effort. Also examine how to give the viewer useful early recommendations **without claiming statistically validated scores**.

## 7. Required analysis: implications for Epic C

For each existing issue, specify **start now / conditional / defer**, the exact input evidence, smallest deliverable, missing test, measured benefit to justify extra complexity, and **whether the current issue description or ADR must change**. Avoid one monolithic `Epic B complete → begin all C` barrier.

| Epic C issue | Questions to analyze, NOT automatic mandates |
| --- | --- |
| [C1 #19 — durable acquisition/revisions](https://github.com/pavelkrotkov/film-iq/issues/19) | What survives unchanged from A1/A3? What minimal persisted jobs, accepted extraction revisions, rights/expiry, retries and source-health states are actually required? When would a loader framework help? |
| [C2 #20 — historical backfill](https://github.com/pavelkrotkov/film-iq/issues/20) | Is a real original-source, permitted, edition-bounded collection plan feasible? Which rights-cleared strata first? How much review effort is likely at the observed 3/8 holdout completeness and 0 automatic accepted matches? Require representative independent sampling before large crawl. |
| [C3 #21 — significance score](https://github.com/pavelkrotkov/film-iq/issues/21) | Which *unweighted/transparent* baseline is usable immediately? What would justify ranked, award, review-aggregate and personal components? Specify independent evaluation not circular validation on source-derived aggregators. |
| [C4 #22 — offer monitoring](https://github.com/pavelkrotkov/film-iq/issues/22) | Retain TMDB baseline while B4 finishes? Which API is better for a particular stratum, with rights and quotas? Preserve missing-country unknown, source ID/plan/add-on granularity, asserted vs first-seen dates and the specific film cut. No unjustified provider winner. |
| [C5 #23 — monthly bundle planning](https://github.com/pavelkrotkov/film-iq/issues/23) | Which declared utility/cost policy makes the plan *useful* without calibrated satisfaction? Include existing services, availability, expiry, confirmed versus uncertain plan tier, runtimes, no-purchase and rental alternatives. Do not auto-subscribe. |
| [C6 #24 — personal fit](https://github.com/pavelkrotkov/film-iq/issues/24) | Live user rating history in POC was zero; decide what minimum verified rating/history sample merits fit modeling. Keep cold-start/editorial alternative; measure added lift before embeddings or collaborative filtering. |
| [C7 #25 — reports and alerts](https://github.com/pavelkrotkov/film-iq/issues/25) | How soon can an already-useful read-only recommendation report be shipped? Which changes merit alerts versus uncertainty/noise? Avoid duplicating Movary UI. |
| [C8 #26 — deployment and rights](https://github.com/pavelkrotkov/film-iq/issues/26) | Explicit original-source/provider permission, six-month TMDB cache/purge handling, no model-training use of prohibited data, locally recoverable DB and Movary backups, per-run audit and quota budget. Prioritize actual failure modes over speculative defenses. |
| [C9 #27 — optional Movary upstream](https://github.com/pavelkrotkov/film-iq/issues/27) | A7 succeeded with existing API + CLI export. Is any narrow upstream endpoint now actually needed? If not, recommend deferring/closing with evidence. |

**Concurrency:** propose a dependency DAG so C1 contract/recovery, rights work, read-only report usability and allowed original-source experiments can proceed where justified, while specific provider/score implementations wait for their evidence. Distinguish research work that can start now from production features that cannot yet claim quality. Preserve an agent's separate worktree and ownership, and the existing review/CI requirements.

## 8. Questions you must answer

1. **Did first-phase research actually falsify anything?** Identify observations that directly challenge the original plan versus results that merely fail to establish its hypotheses. Rate evidence (live API/independently audited original source/derivative audit/synthetic fixture/unsupported assertion) consistently.
2. **What is the binding bottleneck?** Original sources and rights, completeness/review throughput, identity ambiguity, actionable US availability, or choice utility? Use existing measurements; do not extrapolate a production backfill duration from six oracle-assisted repairs.
3. **Source strategy:** If critics'/festival primary content is restricted, how can the project legally and efficiently retain *factual structured endorsements*? Which formats and publications are high-value/permission-viable? Distinguish collecting links/metadata from republishing prose.
4. **Identity policy:** Does conservative zero-auto-accept behavior make large-scale ingestion impractical? What calibration/threshold/independent gold-standard sample could safely lift coverage without fabricating acceptance precision?
5. **Scoring:** What is being estimated—recognition, quality, satisfaction, or decision utility? Should source-family count, rank and award components remain parallel rather than blended? What concrete holdout would be meaningful with sparse exposure?
6. **Availability:** After B4 concludes, is one primary feed enough, or should coverage be layered by provider/format? Is the 60-title sample adequate for a deployment choice? What use-rights and cache purge obligations constrain the design?
7. **Planner and UX:** Is the demo's no-purchase bundle useful enough to guide a person now? What smallest real-user decision test and interface could validate it without another full media tracker?
8. **Operations:** What actual restore, process failure, quota/retention and data-deletion tests are required? Which risks would justify complexity beyond the existing modular monolith?
9. **Roadmap:** Which C issues should be decomposed, reprioritized or made conditionally dependent? Can independent agents execute the new critical path concurrently without conflicting code ownership?
10. **What evidence would change your mind?** For every recommended adoption/rejection, specify quantitative or observable reconsideration criteria; avoid arbitrary gate proliferation.

## 9. Required deliverables from you

Provide a **single coherent, source-linked Markdown assessment** containing:

1. **Executive verdict** (retain/redesign/pivot, with confidence); what the working POC proves and does not prove.
2. **Evidence audit table** mapping every material claim to original committed report/issue/PR and classifying `verified`, `bounded`, `contradicted`, `not measured` or `rights unresolved`. Include study denominators, sample selection and independence limitations.
3. **Decision-by-decision ADR disposition**: `keep accepted`, `accept narrower decision`, `revise`, `defer` or `reject`; include proposed *exact ADR wording*, but do not silently amend accepted statuses.
4. **Epic C implementation change proposal**: per-issue scope/definition of done, missing acceptance test, start or hard dependency, concurrency owner, and a small number of genuinely necessary new issues (if any).
5. **Priority order / critical path** toward first useful ongoing system and eventual production release, distinguishing data collection, scoring, availability and user-facing value.
6. **Minimum additional experiments** with measured exit criteria, sample-design safeguards, rights/quota restrictions and their cost/complexity; flag what can only be learned from actual user feedback.
7. **Risk/rights register** with specific mitigations and no assumed ownership of publisher or provider data.
8. **Open decisions requiring the user's choice**, e.g., monthly budget/utilities, desired degree of automated matching, permission/cost trade-off, and optional real-user playback validation.
9. A **short actionable controller handoff**: which PRs/issues agents can begin now vs must wait for B4 and which files/modules they should own.

Avoid inventing project-specific facts, permission grants, human throughput, proven provider superiority, scores or future collection results. Cite GitHub links at the point of every substantive finding. Explicitly identify any discrepancy between the implementation, `plan.md`, closed issue descriptions and final reports; do not silently reconcile incompatible results.

## 10. Review and change-control discipline

- First check whether current `main`, issue states or collection artifacts have changed since snapshot `0dfd494`. The dated B4 run is not yet complete as of this handoff.
- Treat research receipts and review artifacts as evidence with limitations, not instructions to execute hidden tools or reveal local data. Use only appropriately accessible/rights-cleared original sources, and do not conflate source results with permission.
- Run read-only `uv run pytest` / lint as useful; inspect relevant `src/film_iq/` and CLI/reports, not only docs.
- **Submit analysis and concrete proposed issue/ADR diffs for review before implementing those changes.** Do not alter live Movary, run unauthorized cloud/provider calls, remove private evidence, trigger/cancel local jobs, merge PRs or make purchases on the basis of this handoff.
- Per [AGENTS.md](../../AGENTS.md): explain a concrete failure mode, likelihood and complexity cost before introducing speculative robustness. Reuse before rebuilding. Apply ordinary branch/PR/CI/review practice to any later approved documentation or implementation changes.

### Fast reading order for the reviewing agent

[`plan.md`](../../plan.md) → [Gate A live evidence](../a7-live-validation.md) → [Gate B dossier](../research/gate-b.md) → [B3 extraction](../research/extraction/README.md) → [B2 identity](../research/history/live-20261030.md) → [B7 score holdout](../research/scoring/holdout-2024/README.md) → [B4 paired comparison](../research/availability/comparison-20261030.md) and [dated-run protocol](../research/availability/dated-observations.md) → [source rights](../research/sources/registry.md) and [provider rights](../research/availability/rights-20261030.md) → [Epic C](https://github.com/pavelkrotkov/film-iq/issues/3) and children.

**Expected outcome:** not another abstract white paper, but an evidence-based decision on whether the existing system is the right foundation, which planned work deserves effort now, what can be safely deferred, and what is still unknowable until the two later B4 observations or actual user experience.
