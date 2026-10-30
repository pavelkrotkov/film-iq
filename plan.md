# film-iq — product, research and implementation plan

**Version:** 1.1 (implementation reference) · **Date:** 2026-10-29 · **Status:** approved direction, empirical decisions pending  
**Source:** Film Intelligence white paper v1.0 plus 2026-10-29 architecture/research audit.  
**Policy:** ADRs specify decisions; tracked issues implement them. This document defines scope, expected behavior, milestones and exit criteria, not a claim that implementation exists.

## 1. Why build this?

An individual film viewer wants a durable, explainable way to discover important cinema worldwide (including shorts, documentaries, animation, experimental and less-distributed films) through influential critics' polls, annual lists, festivals and awards. Recommendation quality should improve from ratings recorded in Movary. A separate planning layer should identify legal US viewing options and, when advantageous, a rotating streaming subscription that enables a feasible month of approximately 5–8 films.

Existing trackers, popularity lists, document search and availability websites each address fragments. The distinctive product is **the provenance-preserving join**: critical selection → correctly identified work → independent evidence and uncertainty → personalized priority → verified offer → chosen viewing plan.

The initial user has no organized watched-film history. A completely public-evidence-based launch is required; personalization must not block the first recommendations.

### Product objectives (kept separate)

1. **Critical recognition:** reproducibly represent what specific critics, polls and festivals endorsed, including the provenance, relative strength, eligibility and dependence of evidence.
2. **Personal prediction:** learn whether the viewer will enjoy a film, with separate confidence and exploration that does not erase critical importance.
3. **Viewing decisions:** recommend an achievable, worthwhile monthly set under access, entitlement, time and cost constraints, including doing nothing or renting instead of subscribing.

No weighted sum is declared globally optimal. Evaluate variants against the *relevant* objective. Agreement with aggregators used as inputs is not independent validation.

### Scope and non-goals

| In | Out initially |
|---|---|
| Global film discovery, all formats, 2010–2026 backfill plus older retrospective discoveries | TV-series discovery |
| Historical/current critics' lists and festival/award evidence | Re-hosting licensed criticism or a bulk streaming catalog |
| TMDB/IMDb crosswalk; unresolved-title review | A competing full movie catalog |
| Movary history, rating and watchlist integration | Writing into Movary's database or automatically mass-adding titles |
| US subscription/rent/buy/free/archive/library offer discovery | Automatic service purchases, cancellations and payment actions |
| Transparent reports/CLI and optional alerts | Another general watch-history UI |
| Low recurring cost on existing hardware | Microservices, vector DB or knowledge graph by default |

## 2. Architecture and ownership

```text
Published critical sources → source registry → acquisition + extraction
                                            ↓ validated observations/revisions
TMDB identity/crosswalk ← film-matching ← SQLite evidence + review queue
                                            ↓
                                 versioned public scoring
Movary API + ratings CSV → read-only personal cache → personal priority
                                            ↓
TMDB/JustWatch, alternative offers → normalized current offers + events
                                            ↓
                              feasible monthly plan / CLI / report
                                            ↓ approved actions only
                               Movary watchlist API
```

- **Movary** is source of truth for watched dates, repeated plays, personal ratings, and intentionally saved watchlist entries. It retains the primary interactive UI.
- **film-iq** owns the source registry, original published evidence, identity decisions, scoring and versioning, provider offers, change records, feasibility and planning decisions.
- **TMDB** is the primary external film ID; maintain Movary ID and optional IMDb ID. Never conflate identifiers.
- Internal `radar` / `candidate` / `priority` / `dismissed` are *recommendation* states, not replacements for Movary watched/watchlist states.
- **Runtime:** a Python 3.12+ modular monolith, Pydantic for API/observation boundaries if useful, local SQLite with WAL, scheduled single writer, CLI/reports, and optional very small HTTP layer. Python modules are not separately deployed services. Keep storage local (not WAL on a network share); back up to NAS as desired.
- Require a SQLite build with the documented WAL-reset corruption fix (3.51.3 or backports 3.44.6/3.50.7, or later corrected versions). Enforce foreign keys, deterministic migrations and tested restore.

## 3. Interfaces and integration contracts

### Movary

**POC instance (deployed 2026-10-29):** stock Movary **0.82.1** on Hermes. Open [go/movies](http://go/movies) while connected to the family's Tailscale tailnet. The short link redirects to [Movary on Hermes](https://hermes.tail377b2a.ts.net:8449/); use this full URL if your browser treats `go/movies` as a search. Access is private to the tailnet, over HTTPS; Tailscale must be connected on the device you use.

- **First use:** create the initial administrator on the setup page, then configure a TMDB API key under **Settings → Server**. No account credentials or TMDB key were supplied during installation.
- **Deployment and storage:** `/home/pavel/services/movary` on Hermes contains `compose.yaml`, the secret-bearing `.env`, persistent local SQLite/application `storage/`, and an operations `README.md`. The container restarts automatically unless explicitly stopped. Keep secrets, database files and personal exports out of Git.
- **Operations:** `ssh hermes`, then `cd /home/pavel/services/movary`; use `docker compose ps` for status and `docker compose logs --tail 50` for logs. The local service listens on `127.0.0.1:8090`, with Tailscale Serve providing HTTPS on port `8449`.
- **Verified at deployment:** healthy container, running background worker, access through `go/movies` after restart, and availability of `user:export:ratings`. Movie metadata, authenticated integration, scheduled backups and restoration remain unverified; deployment alone does not satisfy Gate A.
- **Read-only integration recheck (2026-10-29):** SSH and the documented HTTPS endpoint are reachable; the endpoint returns HTTP 200 with the Movary login page, and Docker reports a healthy `leepeuker/movary:0.82.1` container. The documented `.env` exists but contains none of `MOVARY_USERNAME`, `MOVARY_TOKEN`, `TMDB_API_KEY` or `TMDB_READ_ACCESS_TOKEN`; this does not establish whether a TMDB key was configured through the UI. The deployment address/version are known; authenticated API access and movie metadata remain unverified. No credential values were printed and no watchlist write was attempted.

Use published/version-tested `/api/v1` endpoints for paginated played/history and watchlist reads, TMDB movie addition when required, and explicitly approved watchlist additions. Check the installed instance's OpenAPI payloads; distinguish the Movary database ID from TMDB ID. Never write the Movary DB.

**Ratings-only films require a complete ratings path.** Movary 0.82.1 provides `user:export:ratings` CLI and a CSV containing title, year, TMDB ID, IMDb ID and personal rating. The command iterates all rated catalog movies, including those without watched entries. POC: run the export within the self-hosted Movary environment, publish a completed file atomically, then ingest as a replaceable snapshot; a deleted rating must disappear. This avoids a speculative upstream API change. Treat unknown viewing dates as unknown.

Cache watched status, watchlist and ratings for efficient candidate exclusion; caches remain disposable. Every sync records last *successful* snapshot/epoch, errors and version. Provide dry-run, preview, explicit approval and idempotence for every attempted watchlist write.

### Source adapter

A source adapter declares: stable source and edition IDs, original URL, access/rights/retention rules, source family, author/critic, publication time, list eligibility, period covered, ranked/unranked or tied semantics, whether ballots are complete/partial, method/version and accepted document revision.

Each observation records the unmodified raw title and context, optionally original-language title, listed year, director, position, rank and tie, cited text locator, acquisition run, content hash, and extraction decision. Source text grounding is not sufficient by itself: correct rank, author, work identity, eligibility and *completeness* also require validation.

Output is typed and validated; rejected, missing or unresolved observations are retained for review instead of silently dropped. A change in parser must be able to produce a new accepted extraction revision for the same unchanged source document, without creating fresh independent endorsements.

### Provider adapter

Offer observations represent: film, US country, provider/service, subscription vs ad-supported/free vs rent vs buy vs add-on vs library, add-on identity, relevant URL, supplied price/currency, source, observed/checked time, asserted arrival/departure time and confidence/provenance. **Offer identity used by the planner excludes source identity** so duplicate provider reports do not become duplicate opportunities; preserve independent source observations for audit.

Plan entitlement is a separate condition: service-level `subscription` does not prove a title is included on a particular ad-supported tier or on the viewer's account. Preserve `confirmed` / `unconfirmed` / `unavailable_on_plan`; confirm the few offers that drive real purchasing advice on the first-party page and intended plan.

No removal is inferred solely from a failed request, timeout, partial result, unsupported API category or stale cache. `first_seen_by_us` is not a provider-asserted `added_on`. Departure timestamps can be unknown; never invent them.

## 4. Source universe and acquisition

### Starting registry and strata

- **Annual editorial/critic lists:** BFI/Sight and Sound, Film Comment, Cahiers du Cinéma, RogerEbert.com critics, IndieWire, Slant and The Film Stage.
- **Lists-of-lists and retrospectives:** Year-End Lists for lead discovery; TSPDT and BFI long-horizon/decade polls for historical significance. Keep aggregator lineage; avoid double-counting their constituents. Never use source-derived TSPDT agreement as independent proof.
- **Major festivals:** Cannes, Venice, Berlinale, Locarno, Rotterdam, Sundance, TIFF. Model lineup selection, competition inclusion, nomination and prize separately.
- **Specialized formats:** IDFA, CPH:DOX, Annecy, Clermont-Ferrand, experimental and local curatorial selections. Include shorts/experimental documentary/animation in test strata even if metadata or offers are sparse.
- **Geographic diversity:** specifically assess La Internacional Cinéfila and Senses of Cinema World Poll plus other national/local-language critical sources. Track source geography, film geography, language and format separately.
- **Rights/eligibility:** maintain source-level retention and redistribution permission separately from code licensing and from whether web crawling is technically possible.

For each source ask: what universe of films was eligible? were all ballots released? are positions true ranks or merely display order? is the source quoting another? Does the list year mean premiere, local theatrical release, US distribution or viewing year? Film Comment's published partial ballots and TSPDT's derivative aggregates are required adversarial examples.

Backfill two cohorts: **2010–2019** and **2020–2026**, with only actual published 2026 material by date of collection. Add older films referenced in retrospectives. Preserve film premiere year separately from source publication and source eligibility year. Do not indiscriminately push the entire source universe to Movary.

### Extraction hierarchy

1. Official structured API, RSS/Atom, CSV/XLSX.
2. Conditional GET or ordinary HTTP plus deterministic selectors, tables or embedded JSON.
3. Browser-rendered extraction where source rendering actually requires it (optionally Crawl4AI).
4. Grounded or schema-constrained LLM extraction only for difficult prose; verify spans *and* semantics.
5. Human review for ambiguity, incomplete results or parser changes.

Compare the smallest sufficient tool, including pure Python/SQLite loading against dlt on one incremental source. Do not adopt browser, dlt, LangExtract, Huginn or changedetection.io on principle; benchmark accuracy, maintenance, recovery and total work. A single unusual historical page may merit a one-off verified import rather than a generalized crawler.

### Measured extraction pilot

**Epic B owns** the independent **30–40-document extraction benchmark**, covering ranked tables, ties, partial/unranked ballots, translated titles, festival programs, spreadsheets, dynamic pages and unusual formats. Epic A's smaller POC fixtures may be shared into it when available but are not a prerequisite. Freeze manually audited expected observations and hold out pages/layouts not used to develop an adapter. Record precision/recall of source entries, correctness of rank/tie/category, completeness, hands-on correction minutes, runtime/API costs and recovery. A valid 47-object extraction of a 50-film source is a failed completeness result, not a pass.

## 5. Persistence and reproducibility

Use one SQLite DB with acquisition/staging and normalized domain layers:

| Concept | Required fields / invariants |
|---|---|
| `source` | stable ID, family, country, independence group, URL, cadence, rights and health |
| `source_document` | URL, fetch state, hash, accessed/published times, retention policy; raw body only when permitted |
| `source_run` | version, attempt, outcome, last successful check, parser and errors |
| `published_list` | source, edition, author, eligibility, period, rank semantics, completeness, lineage |
| `extraction_revision` | source-document revision, extractor version, validation and acceptance state |
| `list_entry` | stable list/position identity, raw title, director/year, rank/tie, locator, nullable match |
| `film_index` | TMDB, IMDb (optional), Movary (optional), aliases and provenance |
| `match_decision` | raw entry, candidates, method/version, confidence, reviewer and reversibility |
| `award_evidence` / `critic_metric` | film, event/source, type/value/count, dates and lineage |
| `score_snapshot` | algorithm version, independent components, calibration, uncertainty and timestamp |
| `offer_observation` | source-specific normalized observation, access class, entitlement, dates, provenance |
| `offer_current` / `offer_event` | deduplicated opportunity, latest checked, true vs inferred transition distinction |
| `movary_sync` | successful cursor/snapshot, caches, identity map and error state |
| `review_queue` | issue type, original evidence, proposed resolution and audit outcome |

Stable keys, migrations, foreign keys, unique semantic constraints and idempotent transactions. A repeated unchanged acquisition must yield zero new semantic endorsements and alerts. Correcting identity must remap derived effects without erasing the original observation. Cache only data whose permission allows it; implement expiry/purge for provider restrictions. Avoid full global catalog snapshots.

## 6. Film scoring and recommendations

### Critical significance

Do not conflate independent endorsement, award, positive-review percentage, review-score average and audience votes. Initial four-signal mixture **45% lists / 30% professional aggregates / 15% awards / 10% audience** is *illustrative only*, not a committed optimum. Compare at least:

- Independent endorsement count with a recency/release-cohort view.
- Transparent rank-aware score with list eligibility and source-family deduplication.
- Rank-aware score plus awards.
- Above plus appropriately interpreted critic and audience aggregates.
- Full weighted heuristic and at least one no-weights presentation.

Store each component and its original units, sample sizes, data access rights, missingness, calibration and score version. Rotten Tomatoes' positivity proportion is not equivalent to a Metascore. Missing measurements are unknown, not zero. Source independence must account for named critics appearing in multiple lists, derivative list-of-lists and underlying BFI/TSPDT inputs.

Differentiate (a) extraction reliability, (b) identity reliability, (c) breadth/disagreement of critical evidence and (d) uncertainty of personal prediction. Never present one undifferentiated “confidence the film is good”. Sparse niche works remain discoverable, with explicit evidence limits. Normalize exposure and aging cautiously: a 2012 film has more retrospective opportunities than a 2026 premiere, while critics' exposure is rarely observable. A lack of mentions is not a negative review.

Use source-family/period holdouts and human judgments for evaluation. Do not tune to TSPDT and then call agreement with TSPDT independent validation. Show rankings with source links and rationale, including original rank and independence grouping.

### Personal fit

Initially choose from critical evidence alone. Read Movary ratings; optional seed ratings of 20–30 previously seen films can improve cold start but are not mandatory. Learn a simple regularized profile from observed likes/dislikes, film attributes and later, if supported, critic-level agreement. Keep public significance and personalized predicted enjoyment separately visible. Any combined personal-priority heuristic must state its purpose and compare against a non-personalized baseline on time-ordered held-out ratings/selections. Do not treat shown-but-unwatched or passed-over films as negative ratings. Maintain explicit exploration for unfamiliar countries, languages, formats and styles. Embeddings/collaborative filtering require measured improvement before adoption.

### Explainability

Every recommendation must answer: which distinct original critics/lists/awards contributed, exact ranks or types and dates; how duplicate/derivative evidence was handled; how much personal fit influenced the order; what evidence is missing; what legal offers exist and their freshness.

## 7. Availability intelligence

**Baseline:** TMDB/JustWatch watch-provider categories (share upstream lineage with Movary; do not treat that as a second independent confirmation). Verify required JustWatch attribution.  
**Head-to-head comparison:** Movie of the Night's free API with typed subscription, free, rent, buy and add-on offers, deep links and `new/updated/removed/expiring/upcoming` change data. Its change queries use a rolling ~31-day window and future timestamps can be absent. Determine actual account limits and historical retention terms at adoption.  
**Other candidates:** MDBList as an optional joined ratings/availability feed, Watchmode when documented paid functionality is economically justified. Do not pay for change feeds based on marketing claims.

**Benchmark:** at least **60 real films across six strata** (mainstream, international arthouse, older films, documentary, animation, shorts/experimental), sampled on three dates. Compare coverage, access-type correctness, personal-plan entitlement, first-party links, rental/add-on confusion, provider disagreement, update timeliness, quota cost and lack of coverage. A provider returning zero for obscure shorts might still be useful for mainstream films; measure by stratum. Validate availability on the actual desired services (including Criterion and MUBI) rather than headline aggregate country counts.

**Long tail:** official authorized YouTube/Vimeo uploads, distributor/filmmaker sites, PBS/POV, NFB, archive resources and library Kanopy/Hoopla. Search the prioritized candidate universe, not arbitrary YouTube results. Resolve title/director/duration/uploader, full film vs trailer, regional rights and institutional eligibility. Unconfirmed offers remain leads, not guaranteed watchability. Absent titles remain on an unavailable-film radar.

**Polling:** source feeds daily (heavier during year-end), major festivals during events, metadata weekly, top-priority offers every 1–3 days, other watchlist offers weekly, official video discovery weekly/on demand, Movary sync daily/on demand, planning weekly and near decision dates. Tune by quotas and reliability; distinguish fetched-at, observed-since and provider-effective dates.

## 8. Monthly plan and subscription economics

**The choice is a bundle, not a list of attractive movies nor a raw count per platform.** Define a versioned mapping from individual priority to utility of watching a set. A sum, nonlinear high-value weighting, diversity preference and urgency can choose different bundles; validate against actual preference before claiming an optimum.

Let A denote already usable access, O(s) offers from service s, B the time/film capacity, and V(X,B) the highest utility of a *feasible viewing bundle* from access X. Compare:

```text
score(s) = V(A union O(s), B) - lambda * incremental_cost(s)
s in {buy nothing, candidate subscriptions, relevant one-off rentals}
```

Or maximize V under an explicit spending cap. The currency/utility tradeoff is user policy, not derivable from film scores. Marginal value V(A union O(s)) - V(A) is an explanatory metric; candidates must all be compared using the same A and constraints. Duplicate offers do not add another film. Account for current subscriptions, overlap, trial or annual sunk-cost assumptions (where relevant), exact offer types, ad-tier entitlement, rental alternatives and taxes/price if supplied; unknown prices are prompted for, not invented.

A feasible plan respects previously watched status, duration, monthly hours or 5–8 film target, tentative viewing dates versus credible expiry and subscription timing. A film leaving tomorrow cannot be considered safely scheduled for the end of a month. Without a real departure date or account verification, label the plan tentative. Optimize an unconstrained monthly shortlist first; add a small urgent-film feasibility check rather than a full scheduling solver unless needed. Plans may recommend **no additional payment** and fewer films if nothing deserves the time.

Output: recommended service or no purchase; 5–8 or configured films and why; total minutes, platform and entitlement verification, access alternatives, price assumptions, overlap, expiring dates and plausible switch/rental choices. Do not buy, cancel or add titles without user approval. Notify only on meaningful changes; dedupe alerts.

## 9. Operational constraints, rights and safety

- Target zero *new* recurring software/data costs on existing hardware, excluding electricity, equipment and chosen paid streaming subscriptions. Track API quota and requests per useful observation. Paid provider/model requires measured benefit.
- MIT applies to original code only. Crawling technical feasibility is not a redistribution license. Track per-source access, copying, storage duration, attribution, derivative rights and deletion rules.
- Keep personal ratings, API keys, account information, scraped copyright content and full provider datasets out of the public repo. Synthetic/redacted fixtures only where rights permit.
- Include dependency license checks before copying OSS modules. Read actual licenses; Crawl4AI publishes a specific attribution requirement after its Apache text.
- Snapshot backups include **Movary database, complete storage, configuration/secrets, application version**, as well as film-iq SQLite, schema version and config; test restoration.
- Never put live WAL SQLite on NAS/network filesystem; keep local and ship backups. Patched SQLite versions required. Timeouts and bounded retries; report stale data and failures visibly.
- Verify third-party terms before retaining historical observations; Watchmode free-plan caching is time-limited. Do not promise indefinite history independent of provider rights.
- No speculative robustness: explain actual failure mode, likelihood and complexity cost before increasing implementation scope.

## 10. Delivery phases, outputs and decision gates

### Two independent controllers and work handoffs

- **Controller A** owns [Epic A / #1](https://github.com/pavelkrotkov/film-iq/issues/1), application schema and interfaces, source-adapter POC, Movary integration and Gate A. A1–A6 can start concurrently on isolated modules with stubs/fixtures; A7 can begin mocked integration immediately but **closes only after A1–A6 integrate**. A does not wait for B1/B3/B4/B7 results.
- **Controller B** owns [Epic B / #2](https://github.com/pavelkrotkov/film-iq/issues/2), research/source benchmarks, data-rights evidence, and Gate B. B1–B7 can start concurrently from self-selected data and isolated research artifacts; B8 can start a living decision matrix but **closes only after B1–B7**. B does not wait for A1/A3/A4/A5 or A7.
- **No cross-epic hard-blocking edges.** Preliminary source leads, fixtures, provider quality findings and score studies are shared asynchronously through issue comments or versioned research files. Each controller independently owns its GitHub branches/worktrees and avoids simultaneous edits to the other's shared code or documentation. Controller A owns production interfaces; Controller B supplies evidence, proposals and separately scoped benchmark outputs.
- Within an issue, distinguish **starting independent work** from **finishing integration/empirical validation**. Real-data assertions and final closure can have legitimate dependencies even when scaffolding/prototypes do not. Do not allow zero worker utilization because a future integration dependency is open.
- The [GitHub epic and child-issue descriptions](https://github.com/pavelkrotkov/film-iq/issues) are the detailed execution DAG; this plan remains the product/architecture reference.

### Epic A — POC: working vertical slice

**Purpose:** prove the ownership boundary, extraction and identity contract, and one actionable recommendation with a minimal real dataset.

1. Bootstrap repo, CI, tests, source registry schema and redistributable fixtures.
2. Connect unmodified Movary, read watched and watchlist data, generate and import full ratings CSV, test deleted ratings and ID crosswalk, implement approved watchlist dry-run/round-trip.
3. Independently select and audit 4–8 representative POC source pages; implement two to four contrasting deterministic adapters with complete rank/eligibility validation, accepted extraction revisions and review queue. Do not wait for Epic B's broader 30–40-page extraction-method benchmark or final source registry.
4. Resolve sample entries to TMDB; show human-review flow for ambiguous matching.
5. Produce a sourced critical shortlist, baseline TMDB US offers and a **small** “watch this month” report with an explicit plan/no-purchase option (not claimed optimal).
6. Record measurements, unresolved gaps and an architecture gate review; no required upstream Movary changes.

**Gate A:** a reproducible source→film→score→US offer→recommendation→approved Movary write trace; complete rated-only films; no silent truncation, duplicate observations, unapproved writes or false removal claims. Document actual time/cost/error metrics. POC is not the finished discovery backfill or calibrated recommender.

**A7 preliminary finding:** A dry-run and explicit-approval boundary exercises sequential retries against a stub using the published Movary 0.82.1 route contract. The target instance's version and live write semantics remain unverified; no live round trip is claimed. Gate A requires integrated A1–A6 results and explicit authorization for any live write.

**A7 CLI implementation:** The report command opens accepted evidence read-only and renders Markdown or JSON with an explicit identity crosswalk, original/excluded evidence, provider links, freshness, tentative entitlement, plan assumptions and selected-film previews. The sync command defaults to an offline preview; live execution requires both execution/approval flags and local environment configuration. HTTP and CLI paths are mock-tested; no live write has been attempted.

**A2 preliminary finding:** Synthetic fixtures exercise paginated reads and replacement of a ratings CSV, including rated-only films and removed ratings. The installed Movary version, live export, and completeness of an upstream successful export have not been verified.

**A1 preliminary finding:** The SQLite schema records source rights, list-linked extraction revisions, review decisions and source-supplied external IDs; migration and restore fixtures pass on patched SQLite. Independence and lineage verification default to unknown, and current accepted matches are explicit. Real-source rights and downstream integration remain unverified. IDs supplied by a source remain distinct from resolved film identifiers.

**A3 preliminary finding:** One NBR 2023 section has been checked against the original announcement: its winner is ranked, while the other nine titles are alphabetical and unranked. Three Library of Congress selection transcriptions exercise a contrasting unranked format, but are not raw pages or independently audited. The NBR fixture's claimed Wikipedia revision remains unverified. Audited pages, tied and partial examples, rights verification and persisted idempotence remain open.

**A3 source leads:** [BFI's 2022 poll announcement](https://www.bfi.org.uk/news/revealed-results-2022-sight-sound-greatest-films-all-time-poll) describes tied ranks, and [Film Comment's 2024 ballots](https://www.filmcomment.com/best-films-of-2024-individual-ballots/) publishes a selection of ballots. Their [BFI](https://www.bfi.org.uk/terms-use) and [Film Comment](https://www.filmcomment.com/terms-of-service/) terms do not establish permission to commit raw captures. Partial publication of ballots does not establish that a particular displayed ballot is incomplete.

**A3 persistence:** Provisional fixture output can be stored with rights metadata and parser provenance. Repeat ingestion is idempotent; conflicting output fails rather than silently replacing accepted evidence. An explicit independent audit attestation can promote a complete revision; its correctness and independence are auditor claims. Historical human-only wording was an implementation assumption, not issue #6’s requirement. Automated versus human kind must be labelled in the auditor/evidence record. No real fixture has been promoted to accepted.

**A4 preliminary finding:** Synthetic identity decisions and manual corrections persist against the A1 schema with links to extraction revisions. Held-out specialty-film precision, coverage and review rate remain unmeasured; the matching fixtures do not establish real-world accuracy.

**A4 evaluation status:** Five frozen specialty observations and eight CC0 Wikidata candidate leads now have a runnable offline evaluation; four lead retrievals completed and one failed with HTTP 429. Independently audited TMDB truth remains unavailable for all five, so the scored denominator is zero and precision, coverage, review rate and candidate recall remain undefined. `docs/identity-held-out-plan.md` records source locators, preserved discrepancies, rights, retrieval policy and remaining audit gate; `docs/identity-held-out-results.json` records the execution. This does not close #7 or verify the 99% target.

**A5 preliminary finding:** A deterministic baseline counts independent groups and sums reciprocal published ranks; its A1 adapter includes only current matches from explicitly verified original, independent sources. Input snapshots can be replayed with the same scorer version. Real-source verification, richer uncertainty and ranking evaluation remain open.

**A6 preliminary finding:** Synthetic TMDB responses and a small monthly planner exercise offer uncertainty, freshness and no-purchase/rental alternatives. Live provider behavior, terms, entitlement, integration and planner usefulness remain unverified; the planner is limited to small POC shortlists.

**A6 provisional bridge:** The planner resolves internal scoring IDs through the stored film_index TMDB crosswalk and uses `independent-count-additive-v1`: one utility point per independent endorsement. This utility is uncalibrated and ignores rank and personal preference; plan-specific entitlement remains unvalidated. Full cross-issue integration remains in the local integration probe.

**A3 partial-ballot follow-up:** A real incomplete individual assessment was located in Film Comment's 2022 Gina Telaroli ballot, but permission to redistribute a captured fixture remains unverified. No copy was retained. `docs/a6/partial-ballot-lead.md` distinguishes incomplete viewing from editorial truncation and records the remaining narrow fixture gap.

### Epic B — Explore source universe and provider quality

Runs in parallel with POC under its own controller; B1–B7 may all begin independently using their own representative sources, synthetic inputs or benchmark fixtures. B8 can maintain a living draft immediately but finalizes Gate B only after the relevant B1–B7 evidence. No issue in Epic B has a hard start or completion dependency on Epic A.

1. Make a source registry and source-family/eligibility map, including independent critics, polls, TSPDT lineage, international and specialty formats.
2. Build audited historical backfill samples for 2010–2019 and 2020–2026; measure metadata coverage and manual-review burden, including shorts and translation aliases.
3. Own and benchmark the 30–40-page extraction cohort with held-out pages, independently of A3; compare selective OSS module reuse (Kometa/letterboxdpy, GoodWatch and other relevant analogs), rights and maintenance cost.
4. Benchmark 60 films × three dates × six strata against TMDB/JustWatch, Movie of the Night, relevant MDBList feeds and first-party verification; test ad-tier entitlement, long-tail sources, quotas and history rights.
5. Compare public score baselines and derivative-source sensitivity, not just subjective agreement with a source used in training.
6. Publish evidence and decision records: adopted dependencies and APIs, source priorities, permissions and unresolved issues.

**Gate B:** explicit evidence supporting initial source adapters, providers, extraction techniques and scoring approach; publish open questions when evidence is insufficient. This epic is *research work*, not a mandate to integrate every candidate service.

**B preliminary findings (updated 2026-10-30):** Original-source terms can restrict automated collection or reuse. The same critic can appear in multiple publications, so preserve each source and rank while counting independent people once. The fourteen-film historical sample began with cached, derivative or inaccessible catalog results. Its authenticated continuation now records 35 bounded TMDB requests, twelve automated-review acceptances and two ambiguous date-conflicted cases; five of six alternate queries retrieve the reviewed work. These convenience observations cannot establish general coverage or precision. The credential-free dry run still processes all fourteen cases with zero requests. Failed, incomplete and budget-limited searches remain unknown, and no candidate is automatically accepted or declared absent.

The extraction smoke test rejects a 47-of-50 result. One unranked Library of Congress page returned 18 of 18 agent-transcribed titles; its expected observations have not received independent audit. A separate candidate returned HTTP 403 and remains unknown. A supplemental A3 rerun matched 42 records from four derivative Wikipedia sections against an independently automated oracle. A new 32-section Wikipedia corpus has frozen revisions, attribution and a 24-development/8-holdout split. Three independent rendered-source audits enumerated 539 expected records and verified capture metadata. The frozen deterministic baseline passed complete-document checks on 23/24 development sections and 3/8 held-out sections; missing runner-up membership, translated-title disagreement and lost award-year categories remain failures. These are static derivative lists and tables, not coverage of every required source format. Auditors must be identified accurately as automated or human; no human audit or human correction-time measurement is claimed.

A grounded-LLM comparison on one failed development section supplied 12 valid source spans but only 11 scoped memberships; it recovered the missing runner-up and added an out-of-scope directors-poll leader. Scoped precision was 11/12, recall 1, and completeness failed. One case cannot establish comparative method quality. A permitted real-source edition replay loaded ten NBR 2021 selections, attempted eleven 2022 additions, preserved the original ten after an injected source failure, reopened persistent SQLite/dlt state and accepted retry to 21 rows. SQLite made zero writes on an unchanged rerun. One documented run took 0.005 seconds for SQLite and 1.454 seconds for dlt; these tiny replay timings do not establish live incremental performance or process-crash recovery.

A separate Library of Congress PDF first-page supplement matched all 36 independently visually audited factual rows with native PDFKit and a small parser, including a release-year range. It is a bounded historical 1989–2017 registry selection, not a complete or current catalog or a held-out publisher test. A cross-platform retained-text check validates the snapshot but does not exercise PDF extraction. The examined NFB CSV resource could not be acquired because its resource hostname failed DNS resolution; no NFB extraction or availability result is claimed. A separate original CNC CSV under declared Licence Ouverte 2.0 matched all 25 independently audited records in a frozen first-record window, preserving whitespace, unknown director labels and raw administrative dates. The full source stays in ignored cache; the bounded 3,522-byte fixture is not a full-dataset or film-identity accuracy claim. A supplemental two-entity Wikidata query showed a real JavaScript interface rendering rows whose labels were absent from its initial HTML; the interface's documented HTTP JSON API returned the same two rows without rendering. This user-defined query is not an original critic-list or unseen-layout test. Original-publisher browser-only inputs, partial individual-ballot coverage and other untested layouts remain open.

The availability experiment now has a runnable, opt-in TMDB/Movie of the Night observer and 60 machine-readable candidates in six strata. Two automated source audits checked all 60 published work identities and selection context, with pinned encyclopedia revisions and authoritative-source receipts; 64 raw/metadata receipt hashes were checked. Film-year, award edition, premiere and production assertions remain distinct. Duration and country conflicts for shorts are preserved. The public frozen cohort keeps null activation fields. A separate automated audit now supports 60 TMDB work IDs in a local reviewed manifest; date/cut conflicts remain. The first US observation yields 53 usable responses and seven unknown responses in 60 HTTP 200 requests. Movie of the Night, account checks and two further genuinely separate dates remain pending. The dry run still makes zero requests. Offline fixtures exercise failed, partial and truncated responses as unknown. Six long-tail investigations support manual first-party checks and an explicitly inconclusive access outcome; no US playback or personal entitlement was verified. One anonymous player request returned HTTP 401 and remains unknown. OSS reuse findings are qualitative.

Independent PR review found that malformed provider identifiers could be accepted as complete offers. The correction validates TMDB IDs before conversion and requires a nonempty add-on ID; regressions retain the whole response as unknown when a malformed row follows a valid one. The [review and disposition](https://github.com/pavelkrotkov/film-iq/pull/41#discussion_r4420172819) record the evidence. Passing code checks does not complete the outstanding live provider acceptance criteria.

Identity-search review also identified lost diagnostic causes. Failed searches now retain a bounded processing phase, exception class and validated pagination totals without exception messages or credentials. The [diagnostic review and correction](https://github.com/pavelkrotkov/film-iq/pull/39#discussion_r4420208093) include regression evidence. Both correction conversations were resolved after independent re-review and green CI; acceptance gaps remain separate from code correctness.

The scoring study now includes a real ten-film 2008 convenience cohort: three pages yield 61 observed critic selections, while seven have unknown list observations. Independent automated audit found and corrected one omitted unranked selection. Training counts and reciprocal-rank sums favor Milk, while the observed New Yorker held-out rank sum favors The Wrestler. The held-out evidence comprises three critic/film selections across two films. A second independent audit verified reception/context transcriptions for all ten films: RT positivity and critic counts, Metacritic scores and counts, nine RT averages, and four categorical CinemaScore grades without sample sizes. No numeric audience evidence was observed, so the full weighted formula remains unknown for all ten; explicitly renormalized audience-omitted ablations run only on the three list-observed films. Rankings preserve ties. Format and overlapping country missingness are reported, without stability claims. Mixed citation dates and unknown overlap with reception critics prevent temporal-backtest or independent reception-validation claims. The [Gate B working matrix](docs/research/gate-b.md) records evidence and open decisions as the research progresses.

Timing review corrected an import-boundary claim in the loader comparison. Installation is outside both function timers, but SQLite imports precede its timer while dlt can import dependencies inside its timed pipeline construction. The recorded warm-up state is unknown; the original measured values remain unchanged and do not support controlled startup or steady-state comparisons. The [timing finding and disposition](https://github.com/pavelkrotkov/film-iq/pull/35#discussion_r4420403127) distinguish this runner from the historical synthetic implementation that imported dlt before timing.

### Epic C — Final implementation, conditional on gates

Epic C components may start as their **specific** POC or research prerequisites become available; do not force every component to wait for both whole epics to close. Final release still requires accepted relevant Gate A/Gate B evidence and production acceptance criteria.

1. Extend normalized schema, migrations, durable acquisition jobs and event ledger after A/B validate required facts and retention.
2. Scale historical evidence ingestion (2010–2026 and prior retrospective appearances), health monitoring and review workflow.
3. Implement ranked public scoring, confidence dimensions and reproducible snapshots, calibrated against B findings.
4. Implement personalized preference modeling only when Movary ratings and evaluation support it; keep zero-history baseline.
5. Implement chosen availability providers, provider-specific freshness and inferred vs asserted changes, verified entitlements and licensed long-tail alternatives, contingent on B provider decision.
6. Implement transparent bundle utility, budget/no-purchase/rental choices, overlap, urgency, feasible plans and readable reports.
7. Harden backups, restore, deployment, legal compliance, quotas and security; propose only proven upstream Movary enhancements.

**Gate C (release):** a usable 5–8 film or configured monthly plan backed by auditable evidence and correctly classified offers; recovery, accuracy and rights acceptance checks pass. Defer premium providers, LLM infra, graph/vector DB, complex calendar optimization or Movary UI changes absent measured need.

### Proposed acceptance matrix (targets, not achieved)

| Feature | Acceptance evidence |
|---|---|
| Extraction | 100% entries and rank/tie semantics on the *audited fixture cohort*, otherwise review/fail source; report held-out performance and review cost |
| Identity | Aim ≥99% auto-accepted precision on stratified manually checked samples, **also report coverage** and unresolved rate |
| Derivative evidence | Designated poll/aggregator fixtures show no repeated underlying vote |
| Idempotence | Unchanged reruns yield zero new semantic observations, offers/events and alerts |
| Availability classification | Zero known rent/add-on-as-included errors in tested cohort; unknown plan entitlements labeled |
| Removal safety | Failed or partial response cannot create removal; unknown end date not guessed |
| Movary state | Played, watchlist and rated-only records agree after successful sync; intentional watchlist writes require approval |
| Ranking | Baseline variants, source-family/period holds and disagreements documented; objective clearly stated |
| Planner | Feasible bundle vs current access, no-purchase and rental alternatives; time, cost, expiry and verification shown |
| Operations | Clean restore; no secrets/licensed data in repo; permissible retention; API budget and failures observable |

**Evaluation note:** roughly 300 independent correctly audited auto-accepted matches with zero errors have a one-sided 95% binomial lower precision bound near 99%, but clustered/easy-only examples are not independent evidence. This is a sample-design illustration, not a guarantee.

## 11. Dependency decisions and alternatives

**Accepted:** Movary integration rather than rebuild/fork; operational TMDB identity with nullable unresolved matches; relational evidence store; separation of significance and taste; original source records and lineage; minimal CLI/reporting and optional approved sync; no auto-subscription transactions.

**Provisional:** Crawl4AI/LLM/dlt (choose based on extraction benchmark); Movie of the Night vs TMDB availability coverage and quotas; scoring weights or model; introduction of embeddings, UI, advanced scheduling or upstream Movary endpoints. Source registry and provenance are necessary regardless of tool selection.

**Reuse candidates:** GoodWatch (study selected code, not its operationally complex full stack), Cinemagoria (architecture; verify license before copying), Kometa/letterboxdpy (list parsing/ID conversion), Critics Lists Aggregator (scoring reference; check license), PaperSeek (evidence design), MDBList (possible supplemental feed). QMD/OpenKB/Graphiti/Cognee and Huginn are not initially needed. Never assume a hosted-only workflow can retain source and revision detail the product needs.

## 12. ADRs, tracking and references

ADRs are in [docs/adr](docs/adr/README.md), with final vs gated status. GitHub issues are divided into three epics with linked child tasks, explicit dependencies, acceptance criteria and not-yet-decided choices. The initial implementation backlog is *not* permission to override empirical gates.

Primary references (revalidate versions/terms during implementation):

- [Movary](https://github.com/leepeuker/movary), [authentication](https://docs.movary.org/user-guide/api-authentication/), [backup](https://docs.movary.org/backup-and-restore/); [rating export implementation](https://github.com/leepeuker/movary/blob/0.82.1/src/Command/UserRatingExport.php).
- [TMDB watch providers](https://developer.themoviedb.org/reference/movie-watch-providers), [Movie of the Night](https://docs.movieofthenight.com/), [Watchmode pricing](https://api.watchmode.com/pricing), [MDBList API](https://docs.mdblist.com/docs/api).
- [TSPDT](https://theyshootpictures.com/21stcentury.htm), [Film Comment individual ballots](https://www.filmcomment.com/), [Senses of Cinema](https://www.sensesofcinema.com/), [Year-End Lists](https://www.yearendlists.com/category/movies).
- [GoodWatch](https://github.com/alp82/goodwatch-monorepo), [Cinemagoria](https://github.com/cinemagoria/cinemagoria), [Kometa](https://github.com/Kometa-Team/Kometa), [PaperSeek](https://github.com/paperseek/paperseek).
- [Crawl4AI](https://github.com/unclecode/crawl4ai), [LangExtract](https://github.com/google/langextract), [dlt SQLite destination](https://dlthub.com/docs/dlt-ecosystem/destinations/sqlalchemy), [SQLite WAL](https://sqlite.org/wal.html).

## Definition of done for every implementation issue

Issue is linked to an epic and relevant ADR; acceptance tests demonstrate requested behavior; new data fields have origins/rights and migration/rollback; error and review states are explicit; no unapproved writes; docs/config and CI updated; actual measurement or a precise “not yet verified” note attached; PR review and CI requirements in AGENTS.md satisfied.



### Live integration continuation (2026-10-29, UTC 2026-10-30)

The supported Movary `user:list` CLI confirms one existing account. The current
Brave session displays the sign-in form; no existing authenticated browser tab
was found. The account is not assumed absent merely because deployment notes
precede its creation. Sign-in was requested in the prepared tab, without asking
for a password in chat or resetting credentials. Authenticated reads and the
ratings-only export remain pending that access; no personal watchlist was changed.

Public TMDB records are accessible through the actual browser despite prior
fetch-tool robots blocks. Four held-out mappings were checked against visible
catalog titles/creators and frozen primary-source metadata: La Jetée → 662,
Meshes of the Afternoon → 27040, Night and Fog → 803, and A Trip to the Moon /
Le voyage dans la lune → 775. PR #44 merged the separate issue-7 audit overlay and
reproducible measurement: four scored, zero auto-accepts, coverage 0, review rate 1,
conditional candidate recall 1 and undefined precision. #7 is closed against its
implementation/reporting criteria; original frozen inputs remain unchanged. Source
versus catalog year/runtime/name discrepancies remain explicit. This is an
automated factual audit, not human review or evidence of ≥99% auto-match precision.

The public [TMDB/JustWatch US watch page for 775](https://www.themoviedb.org/movie/775-le-voyage-dans-la-lune/watch)
was inspected with United States selected: subscription, free, ads, rent and buy
categories were present. Kanopy requires eligibility verification; HBO Max Amazon
Channel is not proof of inclusion with base Prime. The displayed Amazon rental
was USD 0.99 SD and purchase USD 2.99 SD at inspection; taxes, actual checkout,
playback and personal entitlement were not verified. These are browser-observed
facts, not a captured TMDB API response or a catalog dump.

A bounded source-rights follow-up inspected Rosenbaum, Bordwell/Thompson and
Senses of Cinema leads. None supplied both a verified genuine partial individual
assessment and a verified reusable capture license. Issue #6's narrow gap remains;
public accessibility was not treated as redistribution permission. A subsequent
independent scope audit found that requiring a real partial individual-ballot
capture was stronger than issue #6: its four real pages already include partial
aggregate cases. A focused synthetic partial-individual extraction/persistence
check is being added without changing the real-page count or claiming real
individual-ballot parsing coverage. The actual source-rights limitation remains
documented for broader research, rather than an invented issue-6 closure gate.


### Epic A continuation outcome (2026-10-30 UTC)

PR #44 (browser-audited identity measurements) and PR #45 (partial-assessment
persistence and acceptance-scope correction) are merged. #4–#9 / A1–A6 are now
closed against their actual implementation criteria. Both follow-ups passed
parallel GPT-6.1 Sol High Standards/Spec reviews, required CI and resolved-thread
checks. The latest integrated suite has 294 passes and one opt-in live test skip;
all 109 source/test Python files have maximum CC 8 and minimum MI 50.025. Neither
closure nor the four-case identity measurements verify population accuracy.

The installed Movary 0.82.1 supported `user:export:ratings` CLI was run for the
sole existing account via SSH. PHP's native `php://stdout` with `--silent` streamed
the CSV directly into an ignored, mode-0600 snapshot under this selected project's
`.worktrees/a6-partial-semantics/.cache/movary-live/`; no remote export file was
created. An initial separate-file-descriptor attempt failed; the standard PHP
stream succeeded. film-iq's actual `read_ratings` validated the 36-byte header-only
CSV with zero ratings in 1.39 seconds. Thus real export/schema compatibility is
verified, but a live rated-only record cannot be demonstrated from this empty
ratings snapshot. Fixtures still cover that case; no test rating was invented or
written to the account. No private CSV, account identifier or credentials enter Git.

#10 / Gate A remains open for authenticated paginated API reads, metadata/provider
integration and the concrete selected-film approved write/readback. The current
Brave session is signed out and no account API credential is present in the
documented deployment environment. Sign-in was requested in the prepared Movary
tab; an open browser-extension UI subsequently paused automation. No password was
reset, API credential generated or personal watchlist changed. User sign-in is
required to continue that authenticated path; the deployment location/version are
already known and do not need to be requested again.


### API-only integration handoff (2026-10-30 UTC)

User confirmed browser sign-in and requested API-based integration. The session
is authenticated; browser use was limited to credential/settings discovery.
The installed `/app/docs/openapi.json` and application authentication source
confirm personal API tokens via `Authorization: Bearer` or `X-Movary-Token`;
web-session authentication is separate, and the API source exposes no legacy
web-cookie authentication fallback. A direct unauthenticated GET to
`/api/v1/authentication/token` reached the service and returned HTTP 401.

The current account's Personal API tokens page explicitly reports no tokens,
confirmed after its Refresh API tokens action. The server TMDB credential field
is populated, but its presence does not establish valid Movary API authentication
or TMDB access. No credential was sent to an external metadata API, created,
rotated or revoked. The user reports an existing token; clarification of its
service and existing file/config location was requested. Known project credential
filename patterns returned no configured file. No broader private-folder search
was performed. Authenticated HTTP read tests remain pending the actual Movary
credential; sign-in and endpoint discovery are no longer blockers.

### A3 captured-page continuation (2026-10-29)

Four exact, pinned Wikipedia section responses from distinct source pages now cover
42 published records with ranked, tied, alphabetical/unranked and partial-aggregate
semantics. Two frozen deterministic page adapters match a separate read-only agent's
rendered-HTML oracle. Rights notices, hashes, endpoints and limits are in
[the A6 evidence report](docs/a6/README.md). These are actual API captures, not
transcriptions or whole-page snapshots. All records remain provisional/pending;
a genuine partial individual-ballot fixture remains open. The 2012 title/rank subset
is now corroborated against upstream BFI HTML without retaining it; conflicting
year labels remain unresolved. Independent automated audit is valid within its
stated scope; no human-only gate applies. Explicit acceptance has not been recorded.
No Gate A completion claimed.

**Issue #8 uncertainty followup finding (ADR 0006):** Baseline scores explicitly expose extraction, identity and evidence/disagreement uncertainty as `not_evaluated`, and personal-prediction uncertainty as `not_applicable` without a personal model. Accepted extraction/match status does not imply calibrated reliability, and endorsement/rank totals do not establish disagreement. These fixed defaults serialize with the score and replay from both existing and new v1 input snapshots; input hashes and numeric ranking remain unchanged. The merged PR #32 report now exposes these states in Markdown and JSON. No live accuracy, calibration or personal-prediction validation is claimed.


### Epic A integration and merge findings (2026-10-29)

Implementation PRs #29 (schema), #30 (Movary reads/ratings), #28 (scoring),
#31 (offers/planning), #34 (identity) and #33 (captured-page extraction) have merged
with green CI and resolved review threads. A7 (#32) integrates these modules into
read-only Markdown/JSON reports and a one-selection, explicit-approval sync CLI.
The source and identity issues remain open for their empirical acceptance gaps.

The combined A7 tree passes 291 tests with one opt-in live test skipped; Ruff,
formatting and ty pass. Radon 6.0.1 over all 107 source/test
Python files reports maximum CC 8 and minimum MI 50.025. A duplicated identity-test
setup and callback were simplified to meet the all-files maintainability target;
no production identity behavior was changed. The complete synthetic public-API test now connects persisted extraction, explicit audit, reviewed identity, score, offer, feasible plan, default preview and approved stub write; an unchanged rerun preserves evidence and watchlist state. No new runtime dependency was added.

GPT-6.1 Sol High reviewers posted findings and follow-up reviews on the PRs.
Agreed defects received regression checks, replies and resolved threads. Native
nested parallel agents were unavailable in those review sessions, so their
standards/spec axes were reviewed separately; this is a workflow limitation,
not a claim that the requested nested parallel review ran. No external CI bot
review arrived; all available review conversations were examined.

Gate A is **not accepted**. Remaining evidence includes a redistributable genuine
partial individual-assessment fixture (#6), independently audited TMDB truth and
nonzero scored held-out cases (#7), and target Movary version/export/live semantics
and a real source-to-offer trace (#5/#9/#10). The current five-case identity run
has zero scored cases; unknown truth is not an accuracy result. The actual Movary
instance and authorized local configuration have been requested. No live account
call or watchlist write has occurred. Any selected live write still requires its
preview and explicit approval; merging code does not authorize it. Epic B research
and provisional ADR decisions remain independent.


A separate acceptance audit confirms #4 is complete and it is now closed. The
same audit found that #8 still needs explicit, separate extraction, identity,
evidence/disagreement and prediction uncertainty states under ADR 0006. A small
follow-up is being implemented; no calibration or prediction confidence is claimed.


### Epic A final implementation reconciliation (2026-10-29)

All seven original implementation PRs (#28–#34) are merged. #4 (schema), #5
(Movary reads/export) and #9 (offers/planning with integrated A7 evidence) satisfy
their implementation acceptance criteria and are closed. Their live behavior is
still unverified; closing code issues does not accept Gate A. #8 has a small
follow-up PR #43 for the explicit uncertainty states above. #6, #7 and #10 retain
the documented fixture-rights, identity-measurement and real demonstration gates.

The final PR #32 head received separate **parallel** GPT-6.1 Sol High Standards
and Spec reviews, both clean; prior reviews' nested-agent limitation does not
apply to this final pair. All review threads were resolved and CI was green.
The user's root skill/configuration changes and Epic B worktrees/PRs were preserved.

The #43 integrated tree passes 292 tests with one opt-in live skip (2.04 seconds
locally), Ruff/format/ty and diff checks. All 107 source/test Python files retain
maximum CC 8 and minimum MI 50.025. Legacy v1 snapshot input IDs and numeric
results replay unchanged; new uncertainty fields remain explicitly unmeasured.

### Issue #7 automated browser-audit finding (2026-10-30 UTC)

A separate-from-resolver parent operator inspected four public TMDB records in
the actual user browser. The auditor is `automated:Codex-browser`, not an
independent human; independent GPT evidence-adequacy review is pending. A minimal
[truth-only overlay and reproducible report](docs/identity-browser-audit.md)
preserves differing primary/TMDB years, runtimes and name forms without changing
frozen observations, candidates or earlier results. Existing `evaluate()` scores
four cases: zero auto-accepts, coverage 0, review rate 1, conditional candidate
recall 1, precision undefined. At Land remains unknown/incomplete and excluded.
Recall is conditional on existing Wikidata lead retrieval, not TMDB full-catalog
search. This convenience cohort and automated attestation do not establish
calibrated accuracy, the 99% target, issue #7 closure or Gate A acceptance. No
production identity behavior or ADR decision changes.

### Issue #6 acceptance reconciliation and current status (2026-10-29)

This finding supersedes the historical closure-gate statements above without
rewriting their evidence. Comparing issue #6's exact body and Epic A with this
plan confirms that requiring a licensed real partial individual ballot for #6
closure was an inherited stronger requirement. Four licensed real pages (42
records, two contrasting adapters) cover ranked, tied, unranked and partial
aggregate cases. They remain aggregates/institutional selections, not individual
ballots. One wholly synthetic anonymous individual-ballot case now exercises the
existing extraction-to-persistence interface: eligibility and partial assessment
survive, all published entries and context/locators are stored exactly, unranked
positions remain `rank=None`, document revision/scope survive and reruns make no
database changes. Complete extraction of published content is distinct from
incomplete viewing/assessment; missing films are never inferred. No production
code or abstraction was needed, and the synthetic case adds zero real pages.

These cover the narrow missing semantics assertion under the issue criteria;
parent review/CI still governs closure. A rights-cleared real partial individual
fixture remains a factual coverage gap, and Film Comment adversarial work under
§4 remains open with its rights restrictions and prior research preserved. See
[the corrected evidence report](docs/a6/README.md) and
[research lead](docs/a6/partial-ballot-lead.md). No issue or gate is closed here.

Current parent-reported status: PR #44 merged at `3962fdb`; #4/#5/#7/#8/#9 are
closed against their implementation/reporting criteria. #7 has four audited,
scored cases with zero auto-accepts and undefined precision; no 99% accuracy claim
is made. This supersedes historical notes that identity truth was unavailable
without broadening the convenience cohort's evidentiary scope. #10 and Epic A
remain open pending authenticated reads/export and a real approved round trip.
The browser explicitly requested sign-in; no account token or signed-in session
was available, and opening the extension UI paused automation. No unauthorized
reset or key generation was performed. Root-plan reconciliation remains owned
by the parent; this appendix is confined to this worktree.


### A7 authenticated API validation (2026-10-30)

The user saved the existing Movary personal token in the selected project's
ignored mode-0600 `.env`. Actual HTTP authentication succeeds (200), and the
implemented paginated readers complete for played/history/watchlist with zero
records in each. The earlier live ratings CLI export likewise has zero ratings.
No browser was used for these integration checks and no credential value was
printed. Sign-in/token discovery is resolved.

Movie metadata search returns HTTP 500 through both the implemented backend and
a direct authenticated GET. Targeted application-log inspection and installed
client source identify upstream TMDB HTTP 401 (`TMDB API key is probably not set
or invalid.`). The working Movary credential is separate from this failure.
No configuration fix is claimed yet. An empty `TMDB_API_KEY` slot was added to
`.env` for a valid API v3 key; existing Movary values and mode 0600 were preserved.
A usable key was requested, with the failed live search as the verification loop.

An independent automated auditor verified the original NBR 2023 Best Film award
for Killers of the Flower Moon and its director credit. It is an award category,
not a numeric rank; the film's release year is not inferred from the award edition.
The one-fact original-source scope is explicit. Existing ingestion/acceptance
interfaces stored that factual record, and its unchanged rerun added zero changes.
Identity remains unresolved pending working metadata access; the scorer therefore
has zero eligible matches. No offers/recommendations or live writes were invented.
The isolated final-validation worktree holds the factual audit and current check
report; Gate A still requires verified metadata/offers, a concrete dry run, and
explicit selected-write approval/readback. No personal state was changed.


### A7 real API report and pending approvals (2026-10-30)

The user-provided TMDB v3 key passes direct authentication; metadata/credits and
US provider APIs succeed. The deployed Movary configuration still causes its
movie-search API to fail with upstream TMDB 401. Automatic approval review
rejected sending the key to Hermes and updating/recreating that service without
explicit authorization. The proposed `.env`/Compose change was not executed.

A separate independent automated audit verified Bicycle Thieves at published
**=20** in BFI's 2022 directors' aggregate, with Vittorio De Sica and 1948.
Direct TMDB metadata verifies movie 5156 and 89 minutes. The existing ingestion,
explicit audit acceptance and reviewed identity interfaces produce one independent
scoring group and reciprocal-rank component 1/20. Raw observations are preserved;
unchanged ingestion/automatic replay produce zero new changes. The existing
read-only CLI report leaves the database dump unchanged.

[The real report](docs/a7-real-report.md) includes the default CLI output and a
separate Tubi-only scenario calculated by the existing planner from the actual
US `ads` offer: 89 minutes, one configured 90-minute slot on 2026-11-01, zero
purchase budget and zero incremental purchase cost. No subscription, rental
price or current subscription is assumed. Playback and personal entitlement
remain unverified; provider attribution is TMDB / JustWatch. Full US observations
are retained privately without filtering; the selected scenario is explicit.

The exact dry run is `Preview: add Bicycle Thieves (TMDB 5156) to watchlist`.
[Validation evidence and the proposed operations](docs/a7-live-validation.md)
are reviewable before approval. Remaining steps require explicit authorization:
install the existing saved TMDB key in the documented Hermes deployment and
recreate its same-image service; then use the API to add only movie 5156 to the
catalog if absent and its watchlist entry if absent, read back, and retry for
idempotence. No personal movie/watchlist POST was attempted. Gate A remains open;
no population precision, playback, full paid-plan entitlement or release-readiness
claim is made. The NBR award fact remains a separate unused candidate, without
an invented numeric rank or an assumed film release year.


### A7 approval-ready evidence merged (2026-10-30)

PR #46 is merged at `67ddb2d`. Parallel GPT-6.1 Sol High Standards and Spec
reviews reported no actionable findings, independently checked all five input
hashes, and reproduced both the read-only CLI report and selected Tubi scenario.
All five CI checks passed; local validation was 294 passed/one opt-in live skip,
CC maximum 8, MI minimum 50.025 across all 109 source/test Python files. No
credential was provided to reviewers or included in the committed artifacts.

The explicit pending request was presented for two live steps: persist the
existing saved TMDB key in the documented Hermes deployment and recreate only
the same-image Movary service; then add Bicycle Thieves (1948), TMDB 5156, to the
catalog if absent and watchlist if absent through the existing API boundary,
read back, and retry to verify idempotence. The actual offline preview/report is
reviewable. Automatic approval review rejected the key transfer/configuration
mutation without explicit authorization; AGENTS.md separately requires selected
watchlist approval. Neither elapsed time nor a preselected UI option is approval.
No such authorization or live mutation has occurred at this record point.
Gate A/#10 remains open; no ready implementation PR is being held for review.



### Gate A accepted: approved live round trip completed (2026-10-30)

The user explicitly approved both pending actions. The existing saved TMDB key
was installed in the documented Hermes Movary environment/Compose reference,
Compose validation passed and only the same locally installed 0.82.1 service was
recreated with image pulls disabled. It is running/healthy; the secret file is
mode 0600. Both the selected search and original failed NBR search now complete
through Movary, resolving the previously observed upstream TMDB 401. No runtime
code, upstream fork or dependency change was needed.

The real CLI executed the exact approved Bicycle Thieves (TMDB 5156) preview.
Its observed request order was search GET 200, catalog POST 200, watchlist GET
200, watchlist POST 204. It returned `added to watchlist` in 0.459 seconds.
Authoritative API readback contains TMDB 5156 exactly once, with distinct Movary
ID 1. Repeating the same CLI returned `already on watchlist` in 0.175 seconds;
the retry performed two GETs and zero POSTs and left the watchlist unchanged.
Played/history remain zero and watchlist is one. These are single-run timings,
not benchmarks. No direct Movary database edits or personal rating changes occurred.

[The completed live validation](docs/a7-live-validation.md),
[request/result record](docs/a7-live-write-result.json), and
[healthy configuration evidence](docs/a7-live-configuration-result.json) complete
the original-source → audited observation → reviewed identity → public score →
US offer → configured feasible plan → preview → user-approved API write → readback
trace. The initial read-only/pre-approval artifacts remain explicitly historical;
the selected source, identity and offer snapshot was not rewritten after approval.
Local evidence ingestion/automatic replay and read-only report checks remain
idempotent. Relevant ADRs record measured findings without promoting provisional
provider selection or utility calibration.

**Gate A decision: accept the narrow POC.** Delivery is subject to the final
outcome PR's required CI/review and issue reconciliation. The actual empty ratings
export validates the installed exporter/schema; rated-only and deleted-rating
nonempty cases are fixture-backed, not claimed live-tested. No artificial personal
ratings were written. The held-out four-case precision remains undefined with
zero automatic accepts. Playback, actual preference satisfaction, broad source
and provider accuracy, full commercial/retention rights and restore remain
unverified. Epic B and later release gates remain independent and open; no
uncertain dependency or architecture decision is converted into a final choice.

After the outcome PR passes review/CI and merges, close A7/#10 and Epic A/#1;
all other Epic A children are already closed against their own acceptance criteria.
The user's root configuration/skill edits and Epic B worktrees/PRs are preserved.


Final outcome validation: 294 tests passed, one opt-in live test skipped (2.71
seconds locally); uv-run Ruff/format/ty and diff checks passed. All 109 source/test
Python files retain maximum CC 8 and minimum MI 50.025. The only production Python adjustment is a neutral status message pointing to
plan.md; its existing smoke assertion and operator/README guidance were updated.
No data-read/write implementation or runtime dependency changed. The actual `export_ratings` atomic replacement path
was also exercised twice against the installed supported CLI: identical validated
36-byte/zero-rating snapshots, mode 0600, 2.017 seconds total. Private CSVs and
all temporary files remain in the selected project cache; no remote export file
or personal CSV was committed. This strengthens live adapter/export evidence
without claiming a nonempty live rated-only/deleted-rating test.


### Epic B authenticated TMDB continuation (2026-10-30)

The user configured a project-local, ignored `TMDB_API_KEY`. A read-only
authentication probe returned HTTP 200 / success; no secret value was printed or
committed. The research runners now support TMDB's documented v3 query-key
authentication as a fallback to Bearer authentication, while keeping credentials
out of recorded endpoints and failure diagnostics. The earlier credential
blocker is superseded for TMDB only; Movie of the Night access remains pending.

The frozen fourteen-film historical cohort completed all fourteen searches in
fifteen API requests, including the second page for A Separation. These are
current candidate observations, not accepted identities or an accuracy result.
The completed details/director checks and independent automated adjudication are reported below.
Only selected factual metadata is retained in ignored worktree-local caches;
raw responses/images are not published. The TMDB FAQ supports attributed
noncommercial use; historical retention/redistribution rights are not inferred
from that statement. No provider superiority, account entitlement or Gate B
acceptance is established by successful authentication.

The historical run now includes 14 successful detail/credit requests and six
paired source-alias searches, for 35 benchmark requests in total (21 search,
14 detail). All returned HTTP 200. A separate automated audit supports twelve
identities and leaves two date-conflicted cases ambiguous; this is not human
ground truth or a precision estimate. Five of six source-alias queries retrieve
the reviewed candidate. The romanized Uncle Boonmee alias yields no candidates
even though the English query finds the work, demonstrating why an empty search
cannot establish catalog absence. Automatic acceptance remains zero; human
review minutes and monetary cost remain unknown. The recorded 103.617-second
audit interval is automated elapsed wall time, not human labor.

The availability cohort now has 60 independently automated, evidence-supported
TMDB work identities for offer lookup, with date/cut conflicts retained. Four
broad searches exceeded the five-page budget and remain incomplete despite
positive identity evidence. The local reviewed manifest preserves the original
cohort and audit hashes; it activates TMDB only, with IMDb IDs still null because
they have not been independently verified. B2's conservative date-conflicted
statuses remain separate; neither audit is human precision truth.

B4 made 225 successful TMDB requests: 91 search, 66 detail, 60 first US offers,
seven diagnostic rechecks and one service-label mapping. The earlier 60
restricted-network attempts returned URLError with no confirmed upstream request;
they are preserved separately rather than counted as HTTP failures. All 60
offer requests returned HTTP 200: 53 contain an explicit usable US object and
offers; seven shorts fail schema processing and remain unknown. Seven later
diagnostic rechecks lack an explicit US object. The original failed payloads and
hashes were not retained, so the later rechecks do not prove the original cause. No complete empty-US
response or removal event was observed. The five other assigned strata each
have ten usable responses; shorts/experimental has three usable and seven
unknown. These are assigned reporting strata, not a feature/short partition.
The 529 normalized offer rows are 81 subscription, 218 rent, 204 buy, eight ads
and eighteen free; all account entitlements remain unknown. The catalog sum
13.9719 seconds includes processing, whereas the offer-fetch sum 5.1723 seconds
excludes normalization and pacing. Neither is a total labor/cost measurement.

Three bounded public first-party page checks support title presence at Netflix,
Disney+ and Apple. Web-reader snapshots, generic plan advertisements and a title
page without a transaction/price do not verify US account/ad-tier access or
rent/buy correctness. Duration discrepancies are retained. Movie of the Night
access, historical-retention permission, two further dates, actual account and
transaction checks, and comparative change/expiry measurements remain open.
The updated [B2 review](https://github.com/pavelkrotkov/film-iq/pull/39#pullrequestreview-5711278183)
found no actionable Standards or Spec defects at 8317a76; its empirical gaps remain
explicit. Gate B is not accepted.


### Epic B implementation merge ledger (2026-10-30)

Seven reviewed research/implementation PRs were merged into main. Each merge
commit below is verified in main history; these merges do not accept Gate B or
close an issue by themselves. PR #35 remains the separately reviewed evidence
consolidation. All source worktrees and branches were preserved.

| PR | Merge commit | Merged UTC |
| --- | --- | --- |
| [#36](https://github.com/pavelkrotkov/film-iq/pull/36) | `530051d4ab351e17c456d4e7142e9814b7bd2c1a` | 2026-10-30T12:00:55Z |
| [#38](https://github.com/pavelkrotkov/film-iq/pull/38) | `ff0c7cb43662804d50f765937e7114a3ebd7a4c1` | 2026-10-30T12:00:59Z |
| [#37](https://github.com/pavelkrotkov/film-iq/pull/37) | `49e944bdf50eb268c9641149eae97899d92030c3` | 2026-10-30T12:01:03Z |
| [#39](https://github.com/pavelkrotkov/film-iq/pull/39) | `fa9caa61252811547f0c61065c7687c63aa5f5ff` | 2026-10-30T12:01:06Z |
| [#40](https://github.com/pavelkrotkov/film-iq/pull/40) | `fa441797326cd5b1a511f1f9efac5d080d8191eb` | 2026-10-30T12:01:10Z |
| [#41](https://github.com/pavelkrotkov/film-iq/pull/41) | `af0b41c9df4e56828f1a396a16ad9a1ed7c733cb` | 2026-10-30T12:01:13Z |
| [#42](https://github.com/pavelkrotkov/film-iq/pull/42) | `a6c1416c2d2d30a1a15e215ebc46712d33f481a3` | 2026-10-30T12:01:17Z |

The independent single-PR branches could not be merged by `gh stack merge`: the
first attempt reported that the PR was not stacked, and `gh stack link` requires
at least two branches. The controller therefore used native GitHub squash
merges guarded by each reviewed head SHA and re-read the merged results. This
consolidation was synchronized through gh-stack; its additive plan conflict
retains all A7 and Epic B evidence. Research acceptance remains a separate
issue-by-issue and gate decision.

After synchronization onto main `a6c1416c2d2d30a1a15e215ebc46712d33f481a3`,
the integrated tree passes Ruff, formatting, ty and 333 tests with one opt-in
live test skipped. Radon over all 154 tracked Python files reports maximum
CC 8 and minimum MI 50.025032. No additional runtime dependency or unrelated
code change was needed. The source CSV retains its intentional CRLF bytes; the
diff check permits CR-at-EOL rather than normalizing source evidence.

[TMDB's published rate guidance](https://developer.themoviedb.org/docs/rate-limiting),
checked 2026-10-30, describes an approximate 40-request/second anti-bulk ceiling
that may change and requires respecting HTTP 429. Its old 40-per-ten-seconds
limit was retired in 2019. This guidance is distinct from the account/monthly
quota, cost and retention questions above; no observed quota headers does not
mean unlimited access or zero charges.

### Epic B issue acceptance reconciliation (2026-10-30)

After independent review against the actual issue criteria, the controller closed
[B1 #11](https://github.com/pavelkrotkov/film-iq/issues/11#issuecomment-6522320655),
[B5 #15](https://github.com/pavelkrotkov/film-iq/issues/15#issuecomment-6522322222)
and [B6 #16](https://github.com/pavelkrotkov/film-iq/issues/16#issuecomment-6522323392)
as completed bounded research, with their source PRs merged. Unresolved source
permissions are valid B1 audit findings; unknown playback/library eligibility is
an accepted B5 outcome where testing is infeasible; qualitative adoption cost
satisfies B6 without measured integration hours. None of these closures accepts
Gate B, grants source rights or verifies personal entitlement. Epic #2 remains
open and its three corresponding child checkboxes are updated.

The remaining experiments follow their exact criteria: B2 needs timed manual
review/correction by source stratum; B3 needs measured correction minutes and an
honest boundary for withheld-layout evidence. Preserve the frozen extraction
baseline and record corrections as a separate supplement. B7's New Yorker
source-family holdout was performed and remains valid as a bounded experiment;
its explicit period/diversity holdout still needs an informative extension or an
accepted deferral. Missing numeric audience evidence legitimately leaves the full
weighted formula inconclusive. No human-only identity oracle, mandatory
primary-publisher fetching or broad statistical stability requirement is added.
B4 still requires Movie of the Night access, genuinely separate observation
dates, applicable rights and authorized first-party/account comparisons. B8 #18
and Epic #2 stay open while these non-deferred experiments remain outstanding.
The [working matrix](docs/research/gate-b.md) records concrete next measurements;
no architecture change or additional paid dependency is needed for them.


Final integration against the independently merged Epic B main passed 333 tests
with one opt-in live skip (2.54 seconds locally), plus Ruff, formatting, ty and
diff checks. All 154 tracked Python files, including the merged research code,
have CC at most 8 and MI at least 50.025. Both controllers' plan findings were
preserved; the merge removed no main-branch plan content. The actual approved
live trace still used the previously recorded implementation base; only the
CLI status guidance changed in this outcome PR, not its read/write behavior.


### Epic A delivery complete (2026-10-30)

Final outcome [PR #49](https://github.com/pavelkrotkov/film-iq/pull/49) merged
at `c0f24c583f607dd8daddef1ddfbb470e6cedd72e` after all five exact-head CI
checks passed. Parallel GPT-6.1 Sol High Standards and Spec reviews, plus
integration addenda on `eee7992a5576d12335d77bad708e90cedc28bfad`, found zero
actionable findings; the controller reconciled them on the PR and verified zero
unresolved review threads. No bot findings or pending requested reviewers appeared.
A7/#10 and Epic A/#1 are closed; all children #4–#10 are closed and their
acceptance checklists reconciled. Gate A accepts the narrow POC described above.

The actual approved watchlist write/readback and zero-POST retry are complete;
Bicycle Thieves is present exactly once. Integrated validation remains 333 passed,
one opt-in live skip, CC≤8 and MI≥50.025 across 154 tracked Python files.
Nonempty ratings edge cases remain fixture-backed; playback, entitlement,
population precision, commercial retention and production readiness remain
unverified. Epic B and its provisional decisions remain independent and open.
The user's root configuration/plan edits and existing worktrees are preserved.

### B4 published rights and public quota supplement (2026-10-30)

The [provider ledger](docs/research/availability/rights-20261030.md) traces the
official repository's current terms link to Movie of the Night's native
Developers Platform. The rendered current terms permit local retained data under
use/attribution/third-party-content conditions; the older pinned GitHub TERMS.md
has materially different image and plan provisions and is not applied as the
current native contract. Public native Free pricing is $0 for 1,000 requests per
month, with a hard limit and no overage fees. Three 60-title offer passes budget
180 requests before identity/auxiliary calls and other account usage; the actual
account's plan, remaining quota and charges were not inspected. No API requests,
registration, paid subscription or provider messages were made by this audit.

Native terms specifically prohibit using API data to train, fine-tune, evaluate
or improve ML models or AI systems. The planned availability-provider comparison
is not an AI-model evaluation, and this clause is not treated as a prohibition
on all AI-agent assistance. Future model-training/evaluation data uses need an
applicable permitted basis. TMDB archival rights and actual account terms remain
unverified. This closes part of the public terms investigation, not B4: two later
dates, Movie of the Night access, first-party offers and intended account/ad-tier
checks remain. ADR 0008 remains provisional and Gate B is not accepted.


### B7 period/format continuation and merged follow-ups (2026-10-30)

All eight original Epic B PRs are now merged; the Gate B report merged as
[PR #35](https://github.com/pavelkrotkov/film-iq/pull/35) at
`cee6b3b4c48bad19e94bd415001a24c3f9305cc0`. The reviewed provider-terms follow-up
[PR #48](https://github.com/pavelkrotkov/film-iq/pull/48) merged at
`3d486140ad7744cae118f386af24781c6236e8ff`, documenting current native storage,
attribution and quota terms separately from older repository terms and actual
account state. Issues #11/#15/#16 are closed against their exact research criteria.

[PR #47](https://github.com/pavelkrotkov/film-iq/pull/47) executes the formerly
missing B7 period/diversity holdout. Its twelve 2023–2024 works were frozen before
source acquisition. Fifteen Wikipedia requests preserve failures and a wrong
article before correction; the Wiki-only pass supplies one named-critic selection.
An explicitly exploratory original-list backfill, frozen after that missingness,
adds independently audited NPR/New Yorker selections without replacing films or
tuning weights. Nine distinct critic/film selections cover five works, including
two animated features; a derivative duplicate is counted once. The optional
unverified rank is excluded after the independent source check returned 403.

New Yorker is globally held out by family, including newer writers. Inclusive
typed categories yield three supported overlaps; main-only yields one. Training
counts tie and no training ordinal is observed, so the comparison is inconclusive
for predictive quality. The four shorts remain unknown rather than negative
judgments. Format/country/period denominators are explicit; broad stability and
discovery benefit are not established. This executes the required bounded
experiment, without treating a positive validation result as an invented closure
condition. Acceptance is mapped against #17 separately from Gate B.

The extension adds no dependency or production behavior and preserves the 2008
results. Validation passes 336 tests with one opt-in skip, Ruff/format/ty and
157 tracked Python files with maximum CC 8 and minimum MI 50.025032. The new
research modules/tests alone have maximum CC 7 and minimum MI 51.50. B2's timed
review metric, B3's correction minutes, B4's remaining provider/date/account
measurements and final Gate B synthesis remain open; automated audit wall time
is not represented as human labor.


### B4 paired availability and pre-subscription discovery (2026-10-30)

The [same-date paired report](docs/research/availability/comparison-20261030.md)
now records sixty TMDB and sixty native Movie of the Night HTTP 200 requests:
53 explicit complete TMDB US responses/seven unknown and 49 native complete/
eleven unknown; zero complete-empty. Independent automated review accepts all
sixty work-level lookups while preserving year/runtime/cut uncertainty. A new
local accepted both-ID manifest extends the earlier unchanged TMDB manifest and
is the stable input for later dates; the public cohort keeps null activation IDs.

Source granularity differs: TMDB returns 529 service/category units, native 274
quality variants including 53 add-ons. Explicit nominal mapping covers only
237/529 TMDB units versus all 274 native variants. In 49 jointly complete works,
180 mapped tuples overlap, 51 are TMDB-only and 46 native-only. Unmapped TMDB
units can explain native-only mapped tuples; neither difference is confirmed
absence, error or provider superiority. Add-on hosts, quality, source categories,
free/ads and uncertain tiers remain distinct in retained observations.

Signed-out Netflix/Disney/Criterion pages provide public spot-check evidence;
No Other Land Apple SKU metadata matches three native USD prices, while its
95.87/92-minute runtime conflict remains. Public title pages are benchmark spot
checks, not prerequisites for routine discovery. A separate native Peacock
subscription-catalog query returns twenty rows with `hasMore=true`; this first
page is outside the sixty-film denominator. Peacock publicly advertises
Disclosure Day separately and lists movies in Premium/Premium Plus, not Select;
ad exceptions remain explicit. Consumer login/subscription is unnecessary for
public discovery. Personal entitlement stays unknown by design; any account-specific
validation remains optional and does not block catalog discovery.

This phase adds 60 TMDB/62 native requests (paired pass, native probe and one
Peacock page), plus one public Apple HTTP lookup; browser/web-reader assets are
unmetered. No quota headers or actual account allowance/cost evidence were
returned. All observations remain 2026-10-30 UTC date one. Two genuinely later
dates, change timeliness and unresolved rights/plan-specific classifications
remain; B4 #14, B8 #18 and Gate B stay open, and ADR 0008 remains provisional.
The rights report's native storage/attribution constraints and specific §10
AI-model-use restriction remain applicable; no provider catalog or credentials
are committed. Historical pending-access statements above describe earlier
stages and are superseded only by this bounded continuation.


### B2 source-stratified review effort (2026-10-30)

A [frozen-protocol timed supplement](docs/research/history/review-effort-20261030.md)
performed the manual evidence-review task for all fourteen existing cases in five
primary-source blocks. One agent took 59.235865 seconds across Cannes (nine),
Berlinale (two), Annecy (one), Criterion's derivative retrospective (one) and
Film at Lincoln Center (one). These intervals include reading, reasoning,
tool/model latency and entering decisions; they exclude setup, acquisition,
report/CI work and earlier audits. This is an unblinded repeat review, not human
labor or independent truth: human n=0/minutes null and model billing unknown.
Twelve accepted/two ambiguous decisions remain unchanged, with zero source-field
corrections, zero automatic acceptances and zero new provider requests. Date,
runtime, lineage and local-release uncertainty are preserved. Precision and a
missing-catalog rate remain inconclusive; the review does not create a new
human-only oracle requirement or certify general coverage. Source-frame taxonomy
is reconciled with B1, and festival shorts/translated aliases are the first
recommended expansion. ADRs 0003/0011 and the frozen null-ID sample are unchanged.

### B3 measured correction effort and withheld-layout finding (2026-10-30)

The [post-holdout correction supplement](docs/research/extraction/correction-20261030.md)
froze a protocol before reviewing and repairing all six original failed
documents. Individual UTC/monotonic intervals total 97.345139154 seconds
(1.6224 minutes) of agent-assisted review/correction wall time, including
inference/tool latency; this is not active human labor or billed model cost.
The ledger records one omitted runner-up insertion, 120 award-year/edition
category repairs and one English-title correction with source revisions,
hashes, reasons and before/after metrics. All 151 reviewed records then match
the unchanged independently automated audit. Original parser/audits/results
remain untouched: 23/24 development and 3/8 holdout complete documents.

A post-hoc markup inventory identifies twenty-four rowspan year headers only
in the four failed Academy holdout cases, none in development. This explains
a concrete withheld layout-feature failure; it does not recast the reviewed
corrections or PDF/CSV/dynamic supplements as a new holdout. Named-module
footprints and runtime/maintenance boundaries support deterministic extraction
and SQLite first; heavier framework benefit remains unproven, and lifetime
maintenance, human active minutes and model billing stay explicitly unknown.
B3 closure can use this bounded measured/inconclusive outcome after review;
Gate B still depends on the remaining issue-specific evidence.

### Epic B finish goal and dated-run preparation (2026-10-30)

The explicit finish goal resumes B2/B3 effort measurements in independent
worktrees and B8 decision proposals in parallel. B4's three-date requirement
cannot be replaced by same-day reruns or called completed because a runner exists.
[Dated observation preparation](docs/research/availability/dated-observations.md)
uses native local calendar jobs, the accepted manifest and a minimal UTC date
guard for Oct 31/Nov 1. No credentials are uploaded and consumer login is not
a prerequisite. Installation and actual future evidence must be verified
separately; until then B4/B8/Epic remain open.

The signed-out browser now renders TMDB's canonical API terms, dated 2023-10-20:
six-month cache cap, termination purge and broader ML/AI-application restrictions
are now documented in the [rights follow-up](docs/research/availability/rights-20261030.md).
They supersede the unknown cache duration, not every unresolved applicability or
third-party-rights question. The conservative TMDB study-cache deadline is
2027-04-30. No new API requests, terms acceptance or data deletion occurred in
that terms check.

### B8 prepared choices and explicit finish boundary (2026-10-30)

The [Gate B dossier](docs/research/gate-b.md#prepared-initial-choices-and-final-gate-boundary--2026-10-30)
now makes the initial choices concrete: distinct critic/festival/retrospective
strata with source rights and eligibility intact; native API/HTTP and
source-specific deterministic parsing with transactional SQLite; the existing
TMDB/JustWatch baseline plus native Movie of the Night as a provisional
comparison/discovery candidate; distinct public-scoring components without
selected calibrated weights; and no unsupported larger OSS stack adoption.
ADRs 0005/0006/0008/0012 gain evidence appendices preserving their existing
statuses and required validation. This does not alter production interfaces.

Exact issue reconciliation removes a stale B7 task: #17 is closed after its
performed period/format extension, even though scoring benefit is inconclusive.
B2/B3 effort supplements can proceed now. B4 is genuinely time-blocked on two
later observations: all retained captures are Oct 30 UTC date one. The allowance
for an inconclusive research outcome does not turn missing dates into completed
measurements. No recorded scope deferral exists. B4 #14, B8 #18 and Epic #2
remain open; no consumer-account sign-in or Epic A dependency blocks them.

The dossier names concrete remaining questions for C2 #20, C3 #21, C4 #22 and
C8 #26. It preserves required B4 work rather than silently moving it out of the
epic. If later captures contain no observed changes, report the no-change
interval and unknown change-detection latency without inventing removals,
expiry events, entitlement or a preferred poll interval.

Validation for this docs-only synthesis: Ruff check/format and ty pass;
340 tests pass and one opt-in integration test skips. Radon over all 159
tracked Python files reports maximum CC 8 and minimum MI 50.025032. No code,
dependency, source payload or credential is added by this supplement.


B8 consolidation now includes the fourteen-case, five-primary-source-frame B2
review: 59.235865 seconds of unblinded agent-task wall time, twelve accepted/two
ambiguous unchanged decisions, zero source-field corrections. Human sample size
is zero and human minutes remain null; automatic precision and missing-catalog
rate remain inconclusive. The public TMDB terms follow-up supersedes the prior
unreadable/unknown-cache status with a six-month cap and termination purge.
Broader AI-application and commercial-use conditions need proposed-use
assessment; no coding-agent ban or AI-product permission is inferred.


B3's [separately timed correction supplement](docs/research/extraction/correction-20261030.md)
now covers all six recorded failures in 97.345139154 seconds (1.6224 minutes)
of oracle-assisted agent wall time, including inference/tool latency. It changes
120 category fields, one title field and inserts the missing runner-up, yielding
151/151 exact reviewed records. The original frozen 539-observation benchmark
remains 23/24 development and 3/8 holdout complete documents. A post-hoc inventory
finds twenty-four year-rowspan headers only in the four failed Academy holdouts,
none in development; this explains a real withheld-feature failure without
claiming universal unfamiliar-layout coverage. Human active minutes and billing
remain unknown. B2/B3 supplements are now merged as #51/#54 and issues #12/#13 are closed
after independent review and controller acceptance. B8 consolidates these
results without inventing broader accuracy or cost outcomes.


### Verified Epic B progress and remaining time blocker (2026-10-30)

B2 #12 and B3 #13 are closed after supplements #51/#54 merged at independently
reviewed heads with green PR and merge CI. All six completed B1–B3/B5–B7
research issues retain bounded outcomes and explicit unknowns. The three-date
B4 benchmark remains mandatory; its two unperformed dates are not a deferral.

PR #53 is now merged. Both local Oct 31/Nov 1 observation jobs are registered
in `gui/502` and re-observed with zero runs; no immediate provider calls occurred.
Configurations, logs, receipts and future observations stay inside the approved
project's ignored cache, and no credentials were uploaded. The initial REST
merge response was empty; SHA-guarded native PR merge succeeded and merged state
was re-read. Registration occurred after review/CI, before that fallback merge
confirmation; neither future job ran in that interval. The final dossier
records concrete choices and Epic C questions without accepting Gate B early.

The remaining external/time blocker is actual later-date evidence on Oct 31 and
Nov 1, followed by comparison and final reviewed gate decision. Mac/network
availability is required; missed dates need genuinely later replacements.
No streaming sign-in, purchase or extra credential is requested from the user.

Final consolidated validation before B8 PR review: Ruff check/format and ty pass;
341 tests pass with one opt-in integration skip. All 161 tracked Python files
have maximum CC 8 and minimum MI 50.025032. This synthesis adds no Python code.


B8 combined review: Standards found one stale footprint-scope label; Spec found
no issue with the partial dossier or its preserved finish gate. The 692-LLOC
figure is now explicitly historical/source-version scoped, with a link to the
later named-module counts and correction replay. No new footprint measurement
or runtime change is claimed; the factual documentation correction is checked
against its source report and sent for exact-head follow-up review.


### Local evidence consolidation and worktree-independent observations (2026-10-30)

On the user's cleanup request, private research artifacts were copied into the
explicitly approved `.cache/research-evidence/<worktree-name>/<original-relative-path>`
layout. All 790 selected files (about 26.4 MB) were SHA-256 verified; local
`index.json` preserves old/new paths and branch heads. Rebuildable tool/test
caches are excluded. The cleanup removes old checkouts while preserving every
branch/commit, credentials and research evidence. Public findings remain in
GitHub issues, this plan and the linked reports.

The two Oct 31/Nov 1 jobs now run from root `main` with installed Python 3.12,
the existing `.env` and the unchanged cohort in the consolidated folder. Their
active native registrations contain no worktree paths. Both date guards pass;
a full non-live run emits 120 observations and zero requests. No worktree or
extra retained virtual environment is required for collection. The
[current protocol](docs/research/availability/dated-observations.md) gives paths.
Future measurements remain unperformed; B4/B8/Epic B stay open. This cleanup
does not install an agent wake-up or claim future analysis is automated.

Cleanup review found a manual-command working-directory ambiguity: the paired
example now explicitly enters the main project folder before reading the
consolidated cohort. The native jobs already used that folder; no runtime
behavior or observation result changed.

### First useful personal MVP and two subjective ratings (user direction, 2026-10-30)

**Priority decision:** ship a **small, reliable, rights-appropriate personal discovery companion now**, not a broad publisher article/parser or 2010–2026 bulk backfill. This updates delivery priority, not the final product's wider ambition or the still-open B4/B8 research gates. The existing Movary on Hermes is immediately usable for genuine watch dates, one native personal rating and viewing-date comments. Gate A validated the one-film approved watchlist flow and a header-only real ratings export, **not** a populated two-score feedback loop.

#### Explicit personal and public dimensions

- `personal_enjoyment` (1–10): the user's enjoyment/watchability of a film; **native Movary film rating**.
- `personal_artistic_merit` (1–10): the user's independent artistic judgment; initially a consistently spelled `Artistic merit: N/10` **viewing-date Movary comment**, available as a nullable derived film-level value after testing the pinned `user:export:history` CLI. Different tagged values across repeat viewings are conflicts for review, not last-write-wins. If comment retrieval cannot be verified, use an explicitly labeled temporary private **user-owned CSV** input while retaining Movary's original records.
- `external_critical_recognition`: independent public critic/source/festival evidence; **never** substituted for the user's merit rating.
- `predicted_personal_enjoyment`: optional later modeled estimate, not a user rating. Do not train until enough authentic observations and a time-ordered comparison exist.

Movary documentation lists `userRating` in its **Ratings CSV** and `comment` in its **History CSV**; the latter is attached to a viewing-date entry. Movary 0.82.1 [ships a native history-export CLI](https://github.com/leepeuker/movary/blob/0.82.1/src/Command/UserHistoryExport.php), while the paginated History API omits comments. Its CSV writer repeats a date-entry comment for multiple plays; such repetitions must not become independent/conflicting merit ratings. The existing Film-IQ exporter has live-tested **zero** real rating rows, so a nonempty enjoyment/merit round trip must still be measured. See [ADR 0013](docs/adr/0013-two-personal-scores.md), [ADR 0007](docs/adr/0007-movary-ratings-export.md), and [#58](https://github.com/pavelkrotkov/film-iq/issues/58).

#### First-use MVP issue DAG (independent of full Gate B)

1. **#58 — Real Movary snapshot with two personal scores (start now).** Complete played/history/watchlist API reads, full replaceable ratings CSV, a verified nonempty `user:export:history` comment export or explicit manual merit fallback, real edited/deleted ratings, known/unknown/conflicting merit, no direct DB writes, private local snapshots. Keep the input UI in Movary.
2. **#59 — Small manually curated original-source film cohort (start now).** Import **10–30** selected films from a publisher/edition such as BFI/Sight and Sound *only where proposed access, citation and retention are rights-appropriate*. Use an explicit audited CSV with rank/tie, edition/eligibility, source links as permitted and conservative TMDB identity; do not pretend the selected subset is a complete ballot, scrape general criticism or push candidates to Movary by default.
3. **#25 — First useful read-only shortlist (can scaffold now; integrate #58 + #59).** Include multiple films, source evidence and freshness, both separate personal dimensions, external recognition, watched exclusion, and honestly tentative/no-purchase access. Test user-changed rating and comment refresh plus idempotent reports; no web UI or alerts needed.
4. **Parallel correctness/ops:** scoped C1 #19 source attempt/edition/critic contracts, C3 #21 duplicate critic/rank fix, C5 #23 hybrid/rental feasibility, and C8 #26 rights/backup/restore may begin from Gate A and B1/B3/B7 evidence. Do not block the *first report* on their full production implementations; do require verified recovery/rights before an ongoing production release.
5. **Conditional expansion:** C2 #20 wide source backfill only with source-specific rights and unseen-document completeness; production C4 #22 provider choice only after B4 #14's three actual dates and B8 #18; C6 #24 modeling only with authentic preference data and measured lift; C9 #27 upstream Movary multi-rating feature only if the comment/export workaround is demonstrably inadequate.

**First acceptance test:** user enters 5–15 genuinely watched/rated films (some with merit comments); a complete private refresh makes the exact user-entered 1–10 ratings and comments available without loss, detects changes/deletions, and leaves uncertain values unknown. Import a small independently reviewed source cohort and produce a multi-film, previously-unwatched, explainable shortlist. The displayed report is the first usable product; it is **not** proof of optimum source weights, provider accuracy, real playback or global coverage.

**B4 remains ongoing, not passed:** all retained pairs were dated 2026-10-30 UTC. Two registered Mac jobs are scheduled for 2026-10-31 and 2026-11-01; their registration does not prove execution. Neither the MVP work nor this decision authorizes rescheduling, triggering or stopping those jobs, adopting a provider, or closing #14/#18/Epic B.

**Issue tracking:** [Epic C #3](https://github.com/pavelkrotkov/film-iq/issues/3) and [C0a #58](https://github.com/pavelkrotkov/film-iq/issues/58), [C0b #59](https://github.com/pavelkrotkov/film-iq/issues/59), [C7 #25](https://github.com/pavelkrotkov/film-iq/issues/25). Treat preceding chronological POC/research appendices as historical measured context; these approved priorities supersede the previous all-features-first implementation ordering.
