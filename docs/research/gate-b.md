# Gate B — working evidence matrix

**Status:** In progress, not a gate decision. Updated 2026-10-29.

**Scope:** [Epic B](https://github.com/pavelkrotkov/film-iq/issues/2) and [issue #18](https://github.com/pavelkrotkov/film-iq/issues/18); [plan](../../plan.md#epic-b--explore-source-universe-and-provider-quality); ADRs [0005](../adr/0005-extraction-choice.md), [0006](../adr/0006-scoring-separation.md), [0008](../adr/0008-availability-providers.md) and [0012](../adr/0012-empirical-gates.md).

The table is a working index, not evidence that any issue is complete. Link each report and record its actual sample, errors, labor, costs, rights and unresolved questions as its evidence is reviewed. Gate B requires the relevant B1–B7 evidence or explicit inconclusive outcomes; do not change provisional decisions on preliminary leads alone.

| Issue | Decision or evidence needed | Current status |
|---|---|---|
| [B1](https://github.com/pavelkrotkov/film-iq/issues/11) | Source priorities, eligibility, independence and rights | [Registry](https://github.com/pavelkrotkov/film-iq/pull/36): 11 source entries; source permissions and some eligibility remain unresolved. |
| [B2](https://github.com/pavelkrotkov/film-iq/issues/12) | Historical and specialty-title identity coverage | [Runnable lookup study](https://github.com/pavelkrotkov/film-iq/pull/39): 14 machine-readable cases and opt-in paginated TMDB search; dry run processes 14 with zero requests. Cached/derivative leads remain unresolved. Failure, incomplete pagination and request limits preserve unknown status; no live coverage, accepted matches or precision estimate. |
| [B3](https://github.com/pavelkrotkov/film-iq/issues/13) | Audited extraction cohort, held-out methods and recovery | [Benchmark](https://github.com/pavelkrotkov/film-iq/pull/40): 32 static derivative sections, 539 independently automated-audited expected records. Frozen baseline complete on 23/24 development and 3/8 held-out documents. Grounded-LLM failed completeness despite 12 valid spans (11 scoped memberships). Real-source edition replay preserved ten rows on source failure and retried to 21 after reopening persistent state. Separate historical government PDF first page matched 36/36 independently audited rows. CSV acquisition failed DNS; browser-dependent content remains untested. No process-crash or broad method-quality claim. |
| [B4](https://github.com/pavelkrotkov/film-iq/issues/14) | Provider coverage, offer correctness, rights, cost and change timeliness | [Runnable experiment](https://github.com/pavelkrotkov/film-iq/pull/41): published work metadata/context checked for all 60 candidates, preserving year/duration/country distinctions. Provider-catalog identities remain unverified and activation fields null. Opt-in observer has credential/retention gates, quota/status evidence and offline failure checks; dry run makes zero requests. Live catalog confirmation, credentials, three-date comparison and account entitlement remain pending. |
| [B5](https://github.com/pavelkrotkov/film-iq/issues/15) | Authorized long-tail leads and library eligibility | [Bounded access research](https://github.com/pavelkrotkov/film-iq/pull/37): six investigations and explicit acceptance accounting; manual checks recommended, no adapter justified. One player request returned HTTP 401. Outcome is inconclusive for US playback and individual entitlement. |
| [B6](https://github.com/pavelkrotkov/film-iq/issues/16) | Reuse candidates, licenses and maintenance cost | [Reuse dossier](https://github.com/pavelkrotkov/film-iq/pull/38): pinned module and license inspection; no measured adoption cost. |
| [B7](https://github.com/pavelkrotkov/film-iq/issues/17) | Public-score baselines, independent holdouts and sparse-film behavior | [Scoring draft](https://github.com/pavelkrotkov/film-iq/pull/42): real ten-film cohort, 61 selections across three pages; seven unknown. Independent automated audit corrected one omission. Training count/rank and observed held-out rank-sum ordering disagree across two comparable films. Retrospective selection, shared intermediary and missingness prevent general conclusions. |

## Preliminary constraints

- [Film Comment's terms](https://www.filmcomment.com/terms-of-service/) restrict specified automated collection and reuse. Permission to access a page is not a grant to retain or redistribute its contents.
- [TMDB's movie-provider documentation](https://developer.themoviedb.org/reference/movie-watch-providers) requires JustWatch attribution and does not provide full provider deep links. A service listing is not a verified account entitlement.
- [Watchmode's current terms](https://api.watchmode.com/tc) limit free-plan non-image caching to 30 days and require deletion when the account ends. Apply the actual provider and plan terms before retaining observations.
- [Letterboxd's API policy](https://letterboxd.com/api-beta/) currently excludes several categories relevant to this project, including personal and recommendation projects. An open-source scraper license does not supply source-data permissions.

## Decision record

These are bounded research recommendations, not acceptance of Gate B or changes to production contracts. Cross-cutting ADR decisions remain provisional.

| Component | Outcome supported by current evidence | Remaining evidence |
| --- | --- | --- |
| Source priorities | Prioritize permitted, edition-bounded factual selections and preserve original source families. Restricted criticism/ballots need an appropriate reuse basis before fixture acquisition. Wikipedia copies remain derivative evidence. | Audited original-source eligibility and broader geography/format coverage. |
| Deterministic HTTP extraction | Retain the small HTTP/parser baseline for source-specific experiments, with exact completeness checks and review on failure. The measured 3/8 held-out complete-document rate does not support general unattended extraction. | Additional original publishers and source formats; correction labor. |
| Browser rendering | Inconclusive: the captured sections were statically available. Adding a browser has no demonstrated benefit on this cohort. | A permitted document whose necessary content is absent from raw HTTP. |
| Grounded LLM | No production adoption from the one-case comparison. Valid spans did not prevent an out-of-scope selection or a failed complete-document result. | Independently audited multi-case evaluation, costs and correction effort. |
| SQLite versus dlt | Keep transactional SQLite as the experiment baseline. The edition replay demonstrates retry and persistent-state reopening for both; it does not establish enough incremental benefit to add dlt to production. | Representative job sizes, maintenance/labor costs and process-crash recovery. |
| Availability providers | Insufficient comparative evidence to replace the provisional baseline. Runners and cohorts are preparation, not coverage or entitlement measurements. | Audited IDs, authorized credentials/retention, three observation dates and first-party account checks. |
| Public scoring | Keep weights illustrative. Real observed count/rank disagreement with a tiny held-out sample does not validate a calibrated score or discovery benefit. | Wider independent source/period holds, reception measures, sparse-film and geography/format stability. |

Next work is to complete the prepared identity/provider experiments when their external inputs are available, measure the missing extraction formats and correction effort, and expand the scoring cohort without turning missing selections into negative judgments. No new paid service, crawler platform or production dependency is justified by the current results alone.
