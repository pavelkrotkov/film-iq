# B7 period and format extension — 2026-10-30

This bounded extension executes the period/diversity holdout under [#17](https://github.com/pavelkrotkov/film-iq/issues/17). It does not accept Gate B, validate predictive quality or select weights. The 2008 study and all its results remain unchanged.

## Frozen cohort and source strategy

Commit `ae3d23b127794acb5537379117ca9d50ea0e4dd7` froze the [protocol](protocol.md) and [twelve-film cohort](cohort.json) before source acquisition: four 2024 live-action features, four 2024 animated features, and four 2023–2024 shorts including animation/documentary. No film was replaced after inspecting its evidence. These works are disjoint from the 2008 training pilot.

Fifteen Wikipedia API requests all returned HTTP 200. Two initial responses were API missing-page errors and one resolved to Goose barnacle rather than the film; three ordinary same-agent requests resolved Nickel Boys, Percebes (film) and War Is Over! correctly. All original/corrected receipts remain in [source-receipts.json](source-receipts.json); the final twelve snapshots have revision IDs, hashes and independently checked title/director/year/type context. A successful HTTP response alone did not establish a correct source. Raw snapshots/rendered text remain in ignored local cache, with no images downloaded.

Wikipedia-only evidence supplies one named-critic annual selection: Bob Mondello/NPR for The Brutalist, unranked. Four annual publisher results remain aggregate or unknown-person evidence, never extra independent critics. Positive reviews, filmmaker favorites and institutional awards were not silently converted into personal critic ballots. The four shorts have no observed eligible ballot; that is unknown exposure, not negative relevance.

After this missingness was observed, commit `d552987` froze an explicitly [exploratory amendment](exploratory-amendment.md). It permits original 2024 NPR and New Yorker lists on the same cohort and one optional named critic family. This acquisition strategy is **not preregistered or unseen confirmation**. The cohort, New Yorker family holdout and arithmetic were not tuned.

## Independently audited factual backfill

Ordinary public web-reader access supplied [NPR's Bob Mondello transcript via KGOU](https://www.kgou.org/2024-12-30/the-top-10-movies-of-the-year-according-to-npr-film-critic-bob-mondello), [Richard Brody's list](https://www.newyorker.com/culture/2024-in-review/the-best-movies-of-2024) and [Justin Chang's list](https://www.newyorker.com/culture/2024-in-review/the-best-films-of-2024). Only factual cohort title/author/rank/category metadata is retained; no publisher body, criticism, audio or image is copied. NPR syndication and the Wikipedia carrier are provenance paths, not extra critics. Reader versions may be crawled: labels varied between yesterday and two months ago; no direct body hashes or live completeness guarantee are claimed. NPR warns that its transcript may change and audio is authoritative; audio was not audited.

Separate automated reviewers read the Wikipedia snapshots and original sources without worker rows or scores. The worker froze proposed rows at SHA-256 `f45472002da3974fd4744f1aa6e6363414e5488f2636148946dd42355e736263` before reading their artifacts. Parent communicated the optional source's access failure before that file freeze, without parsed values; this independence limitation is preserved in [audit-summary.json](audit-summary.json). All nine original-source selections matched; the existing Wikipedia/NPR observation duplicates one of them and is counted once. Two introductory mentions are explicitly excluded.

The optional Matt Zoller Seitz individual RogerEbert.com ballot appeared readable in the worker's primary-site search result, but the independent reader returned HTTP 403 twice. Its proposed Nickel Boys rank 9 remains **unverified and excluded from all metrics**; other authors and staff Borda results were not adopted. No access bypass, further family or retry spiral followed.

| Film | Verified training selections, NPR | Held-out New Yorker selections | Category/rank limits |
| --- | --- | --- | --- |
| Anora | 1 | 1 | NPR unranked main; Chang honorable mention |
| The Brutalist | 1 | 1 | NPR unranked main; Chang honorable mention; Wiki duplicate adds no vote |
| Nickel Boys | 1 | 2 | NPR unranked main; Brody 1, Chang 4 |
| Flow | 1 | unknown | NPR unranked main |
| Inside Out 2 | 1 | unknown | NPR additional second-ten recommendation; introductory mentions excluded |

Nine distinct critic/film selections cover five films; ten raw verified carrier observations include the one derivative duplicate. New Yorker is globally held out by **family**, including new writers, rather than filtering only the two 2008 names. Chang's paired discussions do not erase his printed ordinals or create ties. Honorable mentions and supplementary recommendations retain separate categories and no invented rank.

## Conditional results and sparse groups

Run `python -m docs.research.scoring.period_holdout` from the worktree to reproduce [results.json](results.json). The small evaluator reuses the existing `measure()` and tie-preserving `ranking()` baseline. It adds no dependency, production behavior, normalization or fitted weight.

The inclusive typed-selection view has five films with training observations, three with held-out observations, and three supported overlaps. Training counts tie at one for Anora, The Brutalist and Nickel Boys; held-out counts are one, one and two. Training has **zero observed ordinals**, so its rank-aware order is unknown rather than zero. The held-out reciprocal-rank sum is 1.25 only for Nickel Boys; other held-out selections are unranked. This offers no discriminating training rank baseline or calibrated accuracy result.

A main-list-only sensitivity preserves six distinct memberships across four films and only **one** train/held-out overlap, Nickel Boys. The inclusive expansion is category accounting, not permission to treat honorable mentions as top-ten ranks. No weighted formula, reception or award measure was newly acquired or inferred here; the earlier typed reception/award comparisons and unavailable full blend remain as reported in the 2008 study.

| Assigned group | Films | Known training | Known held-out | Inclusive overlaps |
| --- | ---: | ---: | ---: | ---: |
| Live-action features | 4 | 3 | 3 | 3 |
| Animated features | 4 | 2 | 0 | 0 |
| Shorts, all subtypes | 4 | 0 | 0 | 0 |

By source-year, the ten 2024 works have five known training, three known held-out and three overlapping observations; both 2023 shorts remain unknown. These year denominators and the format groups are recorded separately, not treated as calibrated temporal performance.

Source-reported country memberships overlap and are nonadditive; exact country denominators are in results.json. Country is production metadata, not critic origin, story setting or viewer exposure. The two animated positive observations improve format evidence, while all shorts remain unknown. The new period was actually tested, but source sparsity prevents meaningful period/format stability or discovery-benefit estimates. Do not substitute unknown shorts for negative judgments.

## Timing, corrections and rights

The fifteen API request/processing intervals sum to **7.650149 seconds**, including body read, hashing, local snapshot write and JSON/receipt processing, excluding 0.7-second pacing and later model work. Underlying web-reader requests, total model tokens/billing and human correction labor were not metered. Separate automated audit wall intervals were 129.844199 s (Wikipedia), 68.274630 s (NPR/New Yorker) and 28.345705 s (failed optional source). They are not human labor, independent budgets or fair performance comparisons. Per-case assembly intervals do not measure total review effort. Audit dispositions confirmed the tentative NPR attribution and withheld the optional unverified rank; no supported title/rank transcription was changed. All artifact hashes and original proposals are recorded locally and summarized in audit-summary.json.

Wikipedia-derived factual metadata/transcriptions are adapted from **Wikipedia contributors** under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), with revision and history links per source in observations.json/source-receipts.json. Preserve attribution and share-alike for these adaptations; code remains MIT. Original publisher facts have URL/selector attribution, with no inferred license for publisher bodies or future crawling. This report does not grant copying/retention rights. No broad predictive, exposure, satisfaction, calibration or optimal-weight claim follows from these bounded observations.
