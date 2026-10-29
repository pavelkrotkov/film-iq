# B3: Extraction benchmark protocol and synthetic checks

**Version:** 0.1, preliminary. **Date:** 2026-10-29 UTC. **Issue:** [#13](https://github.com/pavelkrotkov/film-iq/issues/13). **Context:** [plan §4](../../../plan.md), [ADR 0005](../../adr/0005-extraction-choice.md), [ADR 0012](../../adr/0012-empirical-gates.md).

One public-domain Library of Congress page has been checked against an agent-transcribed list; it has not received an independent human audit. No 30–40-document audited corpus, browser, LLM or real-source dlt comparison has been completed. The other candidates below are leads only; they are not a frozen gold set or authorization to acquire, store or redistribute source material. No source bodies are included here.

BFI and Cannes URLs are recorded as identifiers rather than active links while their stated linking conditions are reviewed; this is not a legal opinion.

## Runnable synthetic checks

From the worktree root:

```sh
mkdir -p .cache/tmp
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" PYTHONDONTWRITEBYTECODE=1 \
  uv run --no-project --no-config --offline --python python3 -m unittest docs.research.extraction.test_benchmark
```

The four standard-library checks use entirely fictional observations. One removes three of 50 entries: measured entry-key precision is 100%, recall is 94%, and complete-document status is **false**. Others verify that changed title, rank, tie, category or lineage fails despite unchanged keys, that an unranked entry remains unranked, that duplicates fail completeness, and that an empty gold set cannot pass. Entry-key matching assumes independently assigned stable keys; it is not yet a verified real-source identity-matching method. Per-field accuracy covers matched keys only; complete-document status additionally requires exact observations and counts.

The SQLite check loads two fictional rows, repeats an unchanged upsert with zero additional `total_changes`, injects a constraint failure after a changed row and verifies rollback, then retries the correction. This is an in-memory transactional error check, not a process-crash, persisted restart or source recovery benchmark.

The four checks passed locally on 2026-10-29. This smoke test is not representative extraction performance or a comparison of tools. No model/API calls or manual corrections were made by the test.

## One real-source HTTP check

The [Library of Congress public-domain film selection](https://www.loc.gov/free-to-use/public-domain-films-from-the-national-film-registry/) displays 18 items. This is an unranked curated subset, not a complete annual 25-film registry list or an independent critic poll. Its 18 displayed titles were transcribed by the agent from the published page before implementing the parser; they still need an independent human audit. The fixture stores only titles, source URL and revision hash, not the page body or images. The Library's [rights guidance](https://www.loc.gov/legal/security-copyright-and-privacy/understanding-copyright/) distinguishes government works from third-party collection material; do not infer rights for other sources or images from this example.

At `2026-10-29T22:29:41Z`, one HTTP request returned status 200 with a cache-age header of 38,912 seconds. Its SHA-256 was `bd31639eda15cbf1e212bd96d542acd54e880d24b56eedc19b807986c7ae8f7a`. The source-specific standard-library parser returned **18 of 18** transcribed titles: entry precision and recall were both 100%, completeness passed, and display order matched. The list is unranked, so rank/tie accuracy is not applicable. One request and parsing took 0.173 seconds; manual transcription and review time were not measured. These results describe only this revision and page, not held-out performance or general extraction quality.

The offline tests check the selector, entity decoding, incomplete extraction and revision mismatch. To repeat the live check from the worktree root:

```sh
mkdir -p .cache/tmp .cache/uv
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" UV_PYTHON_DOWNLOADS=never \
  uv run --no-project --no-config --offline --python python3.12 \
    python -m docs.research.extraction.loc_baseline
```

A failed request or changed document hash exits as **unknown**, requiring a new audit rather than a negative result. The Library's [robots.txt](https://www.loc.gov/robots.txt) asks general crawlers to leave at least five seconds between requests.

## Optional A3 supplemental sections

On 2026-10-29, the existing [A3 section-adapter tests](https://github.com/pavelkrotkov/film-iq/blob/d08b04a6a1cdf93cc67a4f7f1f50de8f41d9a466/tests/test_page_adapters.py) were independently rerun against four captured Wikipedia sections and A3's separate automated-agent oracle. All eight tests passed. A separate check verified each source-response hash and compared every title, display position, rank and tie with that oracle:

| Captured section | Exact records / expected |
|---|---:|
| NBR 2022 Top 10 Films | 11 / 11 |
| NBR 2023 Top 10 Films | 10 / 10 |
| Sight and Sound 2012 directors' poll | 10 / 10 |
| Sight and Sound 2022 directors' poll | 11 / 11 |

The NBR 2022 section contains 11 selections despite its heading; the Sight and Sound sections are partial excerpts of their underlying top-100 polls. All four are derivative Wikipedia sections, not independent NBR or BFI ballots. A3's oracle was transcribed by a separate automated agent from alternate renderings of the same sections; it is not a human audit. This rerun exercises existing adapters against the same oracle, not held-out layouts, source coverage, acquisition reliability, or a browser/LLM comparison. It does not add A3 as a dependency of this benchmark.

The captures and oracle have [CC BY-SA 4.0 attribution and share-alike requirements](https://github.com/pavelkrotkov/film-iq/blob/d08b04a6a1cdf93cc67a4f7f1f50de8f41d9a466/tests/fixtures/ingest/pages/NOTICE.md); those terms do not grant rights to original BFI/NBR publications or images. No copies of these captures or their oracle are added to this PR. A3's [evidence report](https://github.com/pavelkrotkov/film-iq/blob/d08b04a6a1cdf93cc67a4f7f1f50de8f41d9a466/docs/a6/README.md) records the original-source corroboration and its limitations.

The eight tests can be repeated with the pinned commit available locally, from the B3 worktree root:

```sh
mkdir -p .cache/a3-supplement-d08b04a .cache/tmp .cache/uv
git archive d08b04a6a1cdf93cc67a4f7f1f50de8f41d9a466 LICENSE \
  src/film_iq/__init__.py src/film_iq/ingest/adapters/nbr_2023.py \
  src/film_iq/ingest/adapters/page_capture.py src/film_iq/ingest/adapters/nbr_pages.py \
  src/film_iq/ingest/adapters/sight_sound_pages.py docs/a6/independent-fixture-audit.json \
  tests/fixtures/ingest/pages tests/test_page_adapters.py | tar -x -C .cache/a3-supplement-d08b04a
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" XDG_CACHE_HOME="$PWD/.cache/xdg" \
  UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.cache/a3-supplement-d08b04a/src" \
  uv run --no-sync pytest -q -p no:cacheprovider --basetemp="$PWD/.cache/pytest-a3-supplement" \
  .cache/a3-supplement-d08b04a/tests/test_page_adapters.py
```

## Synthetic SQLite and dlt comparison

An opt-in comparison runs the same two fictional records through transactional SQLite and dlt's SQLAlchemy SQLite destination. Each path loads an initial batch, repeats it unchanged, encounters an injected source failure after one corrected row, verifies the destination still contains the original two records, and retries the correction. The SQLite path checks zero writes on the unchanged rerun; the dlt path checks unchanged semantic rows but does not measure physical writes.

On 2026-10-29, one local run with Python 3.12.15, SQLite 3.54.1, dlt 1.31.0 and SQLAlchemy 2.1.6 reported **0.004 seconds** for SQLite and **2.065 seconds** for dlt. Each measurement includes database/pipeline setup, both initial loads, injected failure and retry; dlt's package import and installation are excluded. The dlt run emitted a SQLAlchemy scalar-subquery warning. This tiny single run is a smoke test, not a representative throughput or maintenance-cost comparison. It did not test a process crash, persisted restart, a real incremental source or actual human correction time.

To repeat it from the worktree root, install the optional comparison dependencies in the worktree-local uv cache and run:

```sh
mkdir -p .cache/tmp .cache/uv
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" UV_PYTHON_DOWNLOADS=never \
  uv run --no-project --no-config --python python3.12 \
    --with 'dlt[sqlalchemy]==1.31.0' --with 'sqlalchemy==2.1.6' \
    python -m docs.research.extraction.dlt_comparison
```

The script disables dlt telemetry, explicitly locates pipeline state and temporary files under the worktree, and overrides dlt 1.31's default global-directory probe for this experiment. Each run leaves its synthetic data in a new directory under `.cache/dlt-comparison/`. This is an experiment-specific adaptation of a pinned version, not a proposed production integration.

## Candidate manifest, not an audited corpus

The suggested split contains **22 development and 12 holdout leads**. Assign a document section and exact expected observations only after confirming access and retention rights. Entire festival PDF programmes and spreadsheets need bounded page or row selections; a confirmed browser-dependent page is still missing.

Development leads (22):

- BFI/Sight and Sound annual top-50 lists for 2022–2025: `https://www.bfi.org.uk/sight-and-sound/polls/50-best-films-2022`, `https://www.bfi.org.uk/sight-and-sound/polls/50-best-films-2023`, `https://www.bfi.org.uk/sight-and-sound/polls/50-best-films-2024`, `https://www.bfi.org.uk/sight-and-sound/polls/50-best-films-2025`. Individual ballots for 2022–2025: `https://www.bfi.org.uk/sight-and-sound/polls/best-films-2022-all-votes`, `https://www.bfi.org.uk/sight-and-sound/polls/best-films-2023-all-votes`, `https://www.bfi.org.uk/sight-and-sound/polls/best-films-2024-all-votes`, `https://www.bfi.org.uk/sight-and-sound/polls/best-films-2025-all-votes`. These are eight page leads. Its terms `https://www.bfi.org.uk/terms-use` restrict copying and deep links; permission and permitted retention remain unresolved.
- Film Comment best films for [2025](https://www.filmcomment.com/best-films-of-2025/), [2024](https://www.filmcomment.com/best-films-of-2024/) and [2023](https://www.filmcomment.com/best-films-of-2023/); undistributed lists for [2025](https://www.filmcomment.com/best-undistributed-films-of-2025/) and [2024](https://www.filmcomment.com/best-undistributed-films-of-2024/); individual ballots for [2025](https://www.filmcomment.com/best-films-of-2025-individual-ballots/), [2024](https://www.filmcomment.com/best-films-of-2024-individual-ballots/), [2023](https://www.filmcomment.com/best-films-of-2023-individual-ballots/), [2022](https://www.filmcomment.com/best-films-of-2022-individual-ballots/) and [2021](https://www.filmcomment.com/best-films-of-2021-individual-ballots/): ten pages. Its [terms](https://www.filmcomment.com/terms-of-service/) prohibit automated cataloging and storage; do not scrape without authorization.
- Cannes official selections for 2025 `https://www.festival-cannes.com/en/press/press-releases/the-films-of-the-official-selection-2025/` and 2023 `https://www.festival-cannes.com/en/press/press-releases/the-films-of-the-official-selection-2023/`, and New York Film Festival main slates for [2025](https://www.filmlinc.org/nyff2025/daily/63rd-new-york-film-festival-main-slate-announced/) and [2024](https://www.filmlinc.org/press/flc-announces-nyff62-main-slate-selections/): four pages. Check terms before any automated acquisition or retained fixture.

Holdout leads (12):

- Three unseen Slant layouts: [2024](https://www.slantmagazine.com/features/the-25-best-films-of-2024/), [2023](https://www.slantmagazine.com/features/the-25-best-films-of-2023/) and [2022](https://www.slantmagazine.com/features/the-25-best-films-of-2022/).
- Four other festival publishers: [Tirana](https://tiranafilmfest.org/official-selection-2025/), [Ulaanbaatar](https://www.ubiff.mn/pinned-news/the-films-for-the-17th-ulaanbaatar-international-film-festival-have-been-announced/), [Brussels shorts](https://bsff.be/en/programme/2025-edition/international-competition/) and [Pollino](https://www.pollinofilmfestival.it/editions/2025-official-selection/).
- Two programme PDFs, [Rotterdam](https://iffr.com/en/wp-content/uploads/sites/2/2025/01/IFFR-2025-Programme-Guide-DEF.pdf) and [Sydney](https://cms.sff.org.au/wp-content/uploads/2026/05/SFF_2026_ProgramGuide_FA_Digital-1.pdf), and the BFI distribution spreadsheet referenced from its site: three unbounded format leads, with storage and redistribution rights unresolved.
- Cannes 2024 `https://www.festival-cannes.com/en/press/press-releases/the-films-of-the-official-selection-2024/` and 2026 `https://www.festival-cannes.com/en/press/press-releases/the-films-of-the-official-selection-2026/`: two page holdouts, **not** unseen-layout holdouts.

An additional uncounted development lead is NEH's [Created Equal page](https://www.neh.gov/initiatives/created-equal). Indexed text contains both four- and five-film descriptions and six related project cards, including an overview, so film membership needs separate verification. NEH's [robots policy](https://www.neh.gov/robots.txt) requests a 300-second crawl delay; no direct page request or benchmark was made here. Its [terms](https://www.neh.gov/privacy-terms-of-use) distinguish generally public-domain federal materials from protected third-party material; fixture rights remain to be checked for the specific content.

Before running, freeze manually audited entries, ranks/ties, membership, source family/lineage and locators, with publisher, document revision, audit date and rights. Keep holdout layouts out of development. Distinguish a publisher's partial selection of ballots, an author's intentionally unranked or partial ballot, and an incomplete extraction. A cited span alone does not validate list membership, rank, identity or category.

## Remaining measurements and decision

For each permitted source and method, record entry precision/recall, per-field correctness, complete-document pass rate, correction minutes, runtime, request/model cost, errors and recovery. Run plain HTTP/selectors first, a browser only where raw HTTP misses required content, and grounded LLM extraction only on cases needing it; check source spans **and** semantic membership. Do not treat inaccessible pages as empty lists.

Extend the two-row comparison to a permitted real incremental source and test persisted restart and retry. dlt's [pipeline documentation](https://dlthub.com/docs/general-usage/pipeline) places state in `~/.dlt/pipelines` by default, so configure the pipeline/state, database, temp and cache paths under the selected worktree before any test, and disable unsolicited telemetry. Its [SQLAlchemy destination](https://dlthub.com/docs/dlt-ecosystem/destinations/sqlalchemy) documents delete-insert and SCD2 merge strategies; measure actual duplicate and correction behavior rather than assuming an upsert. dlt's [Apache-2.0 license](https://github.com/dlt-hub/dlt/blob/devel/LICENSE) does not grant rights to source data.

No dependency, source adapter, or scoring decision is adopted from these synthetic checks. Gate B remains open until the audited corpus and fair comparative measurements exist, or an explicitly inconclusive outcome is documented.
