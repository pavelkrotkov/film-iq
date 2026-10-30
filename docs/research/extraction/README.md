# B3: Extraction benchmark and loader experiments

**Version:** 0.2, preliminary. **Updated:** 2026-10-30 UTC. **Issue:** [#13](https://github.com/pavelkrotkov/film-iq/issues/13). **Context:** [plan §4](../../../plan.md), [ADR 0005](../../adr/0005-extraction-choice.md), [ADR 0012](../../adr/0012-empirical-gates.md).

The frozen static cohort now contains 32 distinct Wikipedia article sections and 539 expected film observations, independently audited by three separate automated agents. A deterministic baseline completed 23/24 development documents and 3/8 held-out documents; its first-run failures are retained. One blinded grounded-LLM experiment recovered an omitted observation but added a cross-poll observation outside the evaluation scope. A persistent SQLite/dlt replay uses two actual captured source editions. These are measured bounded experiments, not evidence for all planned formats, live source reliability, primary-publisher accuracy or production integration. The corpus and audits are licensed separately from the code; see [attribution and limitations](corpus/NOTICE.md).

BFI and Cannes URLs are recorded as identifiers rather than active links while their stated linking conditions are reviewed; this is not a legal opinion.

## Independently audited static cohort

[Selection](corpus/selection.json) fixes one bounded section from each of 32 distinct
articles before the baseline was developed. NBR, Cannes, Berlin, Sundance,
Venice, BFI and BBC sections supply the 24 development cases; Academy, Locarno
and Annecy supply eight held-out cases. All are derivative Wikipedia renderings.
Publisher groups were withheld, but HTML tables/lists can overlap development;
this does not demonstrate unseen-layout or independent-publisher generalization.
The sample includes ranked/tied and partial aggregates, unranked selections,
shorts, animation, documentaries and translated titles. Individual partial ballots,
PDFs, source spreadsheets and browser-dependent pages are not represented here.

The API captures are exact, unmodified section responses pinned to article
revisions, with separately rendered HTML, source wikitext, byte counts,
SHA-256 and UTC retrieval receipts. The retained acquisition used 97 HTTP 200
responses totaling 359,741 bytes, from 03:06:16 to 03:07:56 UTC on 2026-10-30;
that interval includes the deliberate 0.7-second inter-request delay. Additional
discovery calls were not timed as an end-to-end acquisition benchmark. No
authentication or billed provider/model API was used to acquire the corpus.

Three independent agents read only their rendered source sections, receipts,
revision metadata and rights declarations: [audit 1](corpus/audit_group1.json),
[audit 2](corpus/audit_group2.json), [held-out audit](corpus/audit_holdout.json).
They did not see wikitext, parser output, tests or other audits. Each enumerated
and reviewed every source film row, displayed position, numeric rank/tie and
section/subgroup category. These are explicitly **automated audits**, not human
attestations or independent original-publisher corroboration. They verify
captured derivative observations, not catalog identity, release eligibility or
award-winner status. Hands-on human correction minutes were not measured.

The [parser freeze](corpus/baseline-freeze.json) precedes the first held-out run.
No parser changes were made after reading the oracle or held-out content.
[First-run results](corpus/static-results.json) retain every extracted record:

| Split | Documents complete | Expected / extracted / matched titles | Exact full records | Parser seconds |
|---|---:|---:|---:|---:|
| Development | 23 / 24 | 334 / 333 / 333 | 333 / 334 | 0.0453 |
| Held out | 3 / 8 | 205 / 205 / 204 | 84 / 205 | 0.0206 |

Full-record correctness includes title, position, rank, tie and category; a
document passes only if all records and their order match the independent audit.
Entry precision/recall and per-field correctness for each document are recorded
in the JSON. Per-field matches require the displayed title plus that field to
match, divided by all expected records; missing titles remain failures. A high title recall therefore cannot conceal category failures.
The baseline omitted the explicit *Battleship Potemkin* runner-up outside the
critics' ordered list. On held-out tables it omitted Academy year/award-edition
subgroups for all 120 nominee records, and chose an italic original title instead
of the unitalicized English *The Infernal Machine* in one Locarno row. Those
failures remain failures, with no post-holdout tuning or narrowed gold set.

Repeat offline from the worktree root:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" UV_PYTHON_DOWNLOADS=never \
  uv run --no-sync python -m docs.research.extraction.corpus_run
```

The runner rejects changed source bytes, mismatched oracle revisions, a changed
frozen parser and incomplete oracle coverage. It returns measurements including
failed documents; successful execution is not a completeness pass.

## Bounded grounded-LLM comparison

A fresh, blinded agent received only the original `poll-0` source section,
receipts and scope, without parser, oracle, results or an omission hint.
[Its raw extraction](llm_poll0.json) contains 12 positive observations with
exact source quotes/line ranges. A protocol deviation exposed the full selection
metadata, but no other captures or outcomes. Exact model identity, total tokens,
billed cost and full elapsed extraction time were not available and remain
unknown; the output records its measured in-progress/end timestamps.

[Independent span and semantic checks](corpus/llm-results.json) found 12/12 quotes
present at their cited source lines, yet only 11/12 observations belong to the
audited critics-selection scope. The additional directors-poll leader is a
supported cross-poll assertion, not a fabricated title, but is outside that
evaluation scope. Compared with the static baseline's precision 1, recall 10/11,
the LLM has precision 11/12, recall 1 and still fails complete-document status.
The checker normalizes its declared `tie=false` to no tie and its runner-up
subcategory to the audited subgroup; it retains the extra observation. Source
spans alone therefore do not justify accepting semantic membership or adopting
an LLM extraction framework. Repeat with
`uv run --no-sync python -m docs.research.extraction.llm_check`.

## Original-source PDF supplement

A separate [Library of Congress PDF experiment](formats/README.md) acquired an
original historical Registry list and independently audited its first page from
the visual rendering. Native PDFKit extraction matched all 36 displayed title,
release-year/range, induction-year, position and category records. This is an
additional development-format check, separate from the frozen 32-section cohort
and its first-run rates. It uses a born-digital government table, without OCR or
a browser. The cross-platform CI check verifies a saved text snapshot against
the visual oracle; it does not exercise PDFKit on Linux. The supplement records
source rights, transformation hashes, single-run timings and a failed original
CSV acquisition as unknown. Source spreadsheets, browser-dependent pages and
general PDF-programme performance remain unmeasured.

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

The [Library of Congress public-domain film selection](https://www.loc.gov/free-to-use/public-domain-films-from-the-national-film-registry/) displays 18 items. This is an unranked curated subset, not a complete annual 25-film registry list or an independent critic poll. Its 18 displayed titles were transcribed by the agent from the published page before implementing the parser; they still need an independent audit. The fixture stores only titles, source URL and revision hash, not the page body or images. The Library's [rights guidance](https://www.loc.gov/legal/security-copyright-and-privacy/understanding-copyright/) distinguishes government works from third-party collection material; do not infer rights for other sources or images from this example.

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

## Persistent real-source edition replay

The same loaders also replay the independently audited NBR 2021 and 2022
sections: ten initial observations and eleven new-edition observations, keyed by
captured edition and displayed position. This key is only a frozen-replay key,
not a proposed production identity or cross-revision correction key. The input
uses the independent oracle so extraction failures do not confound loading.

Each path persists the initial ten, reopens its SQLite connections or reconstructs
the dlt pipeline at the same state path, repeats the input, then receives an
actual new-edition row followed by an injected source-iterator exception.
The destination must still contain only the original ten. After another reopen
or pipeline reconstruction, retry succeeds with exactly 21 observations. The
SQLite unchanged rerun performs zero writes; dlt semantic rows are unchanged,
but its physical writes were not measured. This exercises persisted state and
source-failure recovery, not a killed process, live incremental API, spontaneous
publisher correction or arbitrary failure during database commit.

[Recorded validation run](corpus/loader-results.json): Python 3.12.15, SQLite
3.54.1, dlt 1.31.0 and SQLAlchemy 2.1.6; SQLite took 0.005 seconds and dlt 1.454
seconds. These are one tiny replay's setup/load/retry measurements, excluding
package installation/import; they are not throughput or maintenance-cost
estimates. dlt emitted the same SQLAlchemy scalar-subquery warning as the
synthetic experiment. No source polling or model API was used.

With the optional pinned dependencies installed, repeat from the worktree root:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" UV_PYTHON_DOWNLOADS=never \
  uv run --no-project --no-config --python python3.12 \
    --with 'dlt[sqlalchemy]==1.31.0' --with 'sqlalchemy==2.1.6' \
    python -m docs.research.extraction.real_incremental
```

Pipeline state, databases, caches and temporary files stay under the worktree's
`.cache/real-incremental/`; telemetry is disabled. The same experiment-specific
global-directory adaptation described below applies to the pinned dlt version.

## Earlier synthetic SQLite and dlt comparison

An opt-in comparison runs the same two fictional records through transactional SQLite and dlt's SQLAlchemy SQLite destination. Each path loads an initial batch, repeats it unchanged, encounters an injected source failure after one corrected row, verifies the destination still contains the original two records, and retries the correction. The SQLite path checks zero writes on the unchanged rerun; the dlt path checks unchanged semantic rows but does not measure physical writes.

This historical smoke result predates the persisted reconstruction steps added for the real-source replay; its [original implementation](https://github.com/pavelkrotkov/film-iq/blob/e43eaf6050e2105bf02b04b71843978b58390c79/docs/research/extraction/dlt_comparison.py) is pinned separately. On 2026-10-29, one local run with Python 3.12.15, SQLite 3.54.1, dlt 1.31.0 and SQLAlchemy 2.1.6 reported **0.004 seconds** for SQLite and **2.065 seconds** for dlt. Each measurement includes database/pipeline setup, both initial loads, injected failure and retry; dlt's package import and installation are excluded. The dlt run emitted a SQLAlchemy scalar-subquery warning. This tiny single run is a smoke test, not a representative throughput or maintenance-cost comparison. It did not test a process crash, persisted restart, a real incremental source or actual human correction time.

To repeat it from the worktree root, install the optional comparison dependencies in the worktree-local uv cache and run:

```sh
mkdir -p .cache/tmp .cache/uv
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" UV_PYTHON_DOWNLOADS=never \
  uv run --no-project --no-config --python python3.12 \
    --with 'dlt[sqlalchemy]==1.31.0' --with 'sqlalchemy==2.1.6' \
    python -m docs.research.extraction.dlt_comparison
```

The script disables dlt telemetry, explicitly locates pipeline state and temporary files under the worktree, and overrides dlt 1.31's default global-directory probe for this experiment. Each run leaves its synthetic data in a new directory under `.cache/dlt-comparison/`. This is an experiment-specific adaptation of a pinned version, not a proposed production integration.

## Original primary-publisher candidate leads

This original proposal is separate from the captured static cohort above and is not its gold set. The suggested primary-publisher split contains **22 development and 12 holdout leads**. Assign a document section and exact expected observations only after confirming access and retention rights. Entire festival PDF programmes and spreadsheets need bounded page or row selections; a confirmed browser-dependent page is still missing.

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

## Supplemental dynamic interface

A separate [Wikidata Query Service experiment](dynamic/README.md) exercised a
real JavaScript interface with a deliberately defined two-film query. Neither
observed result label appeared literally in the initial HTML. The browser
rendered both rows; the interface's documented HTTP JSON endpoint returned the
same two IDs and labels without browser rendering. Retained CC0 data, request
receipts and automated cross-surface observations are linked from that report.
This supports the native API for this query, not a general publisher, browser
framework, completeness or timing claim. It is not part of the frozen static
holdout or an original critic-list sample.

## Remaining measurements and decision

Radon 6.0.1 measures **645 logical Python lines including tests** across the
changed research modules and pytest wrapper. This is a code-footprint measure,
not an estimate of engineering labor, JavaScript/native-engine size or total
maintenance cost. Human correction minutes and full model billing remain
unmeasured; the single-run timing boundaries are stated with each experiment.

| Component | Bounded recommendation from these observations |
|---|---|
| Stdlib static selectors | Retain as the first attempt with explicit completeness review. The measured 26/32 full-document result does not justify automatic acceptance across sources. |
| Browser rendering / Crawl4AI | The supplemental dynamic query interface rendered two rows missing from its initial HTML, but its native HTTP API supplied the same data. Use that API for this case; no framework or original-publisher generalization is demonstrated. |
| Grounded LLM / LangExtract | The single agent run improves recall but introduces an out-of-scope record despite valid spans. Keep semantic review; framework benefit, model cost and repeatability remain unmeasured. |
| Transactional SQLite | Smallest demonstrated loader for this 21-observation replay, including zero unchanged writes and persisted retry. No production-scale performance claim. |
| dlt | No adoption justified by this replay: both paths recover, while dlt adds dependencies, state configuration and a warning. Its broader connectors and larger-job benefits were not measured. |

For each permitted source and method, record entry precision/recall, per-field correctness, complete-document pass rate, correction minutes, runtime, request/model cost, errors and recovery. Run plain HTTP/selectors first, a browser only where raw HTTP misses required content, and grounded LLM extraction only on cases needing it; check source spans **and** semantic membership. Do not treat inaccessible pages as empty lists.

Further evaluation should use a live, rights-permitted incremental source and test a killed process or failure during commit; the captured-edition replay above only exercises source-iterator failure and persisted reconstruction. dlt's [pipeline documentation](https://dlthub.com/docs/general-usage/pipeline) places state in `~/.dlt/pipelines` by default, so configure the pipeline/state, database, temp and cache paths under the selected worktree before any test, and disable unsolicited telemetry. Its [SQLAlchemy destination](https://dlthub.com/docs/dlt-ecosystem/destinations/sqlalchemy) documents delete-insert and SCD2 merge strategies; measure actual duplicate and correction behavior rather than assuming an upsert. dlt's [Apache-2.0 license](https://github.com/dlt-hub/dlt/blob/devel/LICENSE) does not grant rights to source data.

No production dependency, source adapter or scoring decision is adopted by this research PR. The component recommendations above are bounded by the actual measured formats and costs; untested formats and live-source reliability remain open.
