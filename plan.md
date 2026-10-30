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

### Epic B — Explore source universe and provider quality

Runs in parallel with POC under its own controller; B1–B7 may all begin independently using their own representative sources, synthetic inputs or benchmark fixtures. B8 can maintain a living draft immediately but finalizes Gate B only after the relevant B1–B7 evidence. No issue in Epic B has a hard start or completion dependency on Epic A.

1. Make a source registry and source-family/eligibility map, including independent critics, polls, TSPDT lineage, international and specialty formats.
2. Build audited historical backfill samples for 2010–2019 and 2020–2026; measure metadata coverage and manual-review burden, including shorts and translation aliases.
3. Own and benchmark the 30–40-page extraction cohort with held-out pages, independently of A3; compare selective OSS module reuse (Kometa/letterboxdpy, GoodWatch and other relevant analogs), rights and maintenance cost.
4. Benchmark 60 films × three dates × six strata against TMDB/JustWatch, Movie of the Night, relevant MDBList feeds and first-party verification; test ad-tier entitlement, long-tail sources, quotas and history rights.
5. Compare public score baselines and derivative-source sensitivity, not just subjective agreement with a source used in training.
6. Publish evidence and decision records: adopted dependencies and APIs, source priorities, permissions and unresolved issues.

**Gate B:** explicit evidence supporting initial source adapters, providers, extraction techniques and scoring approach; publish open questions when evidence is insufficient. This epic is *research work*, not a mandate to integrate every candidate service.

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
