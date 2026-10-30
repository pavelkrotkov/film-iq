# B2: historical source and identity sample

Version 0.1 · Source checks 2026-10-29 · [Issue #12](https://github.com/pavelkrotkov/film-iq/issues/12) · [Epic B](https://github.com/pavelkrotkov/film-iq/issues/2)

**Dated continuation:** [The 2026-10-30 live search and detail experiment](live-20261030.md)
supersedes the historical no-live-request status below. It preserves the original
fourteen-case sample and its unresolved source contexts; a successful catalog
response alone does not establish a correct film match.

**Timed supplement:** [The source-stratified review-effort report](review-effort-20261030.md) records an actual unblinded agent-assisted review of all fourteen cases. Its 59.235865-second wall time is separate from still-unmeasured human labor; the earlier sample and outcomes are unchanged.

This is an exploratory, convenience-selected sample, not a representative catalog benchmark or a completed acceptance test. It spans the target periods and older retrospectives, with translated titles, documentaries, animation and shorts. The source pages were inspected using a web search/reader; their displayed records can change and are not permission to copy or redistribute the underlying source text. Only concise identifiers, links and findings are recorded here. [Plan §4](../../../plan.md) and [ADR 0003](../../adr/0003-film-identifiers.md) require keeping original evidence and unresolved matches rather than forcing an ID.

Cannes URLs are recorded as identifiers rather than active links because its `https://www.festival-cannes.com/mentions-legales/` states conditions on links; this records the stated condition, not a legal opinion.

**Do not infer current coverage from this sample.** The accessible TMDB pages below were search-reader snapshots labeled roughly 1.3 years old, not fresh API responses. The expected `TMDB_API_KEY` and `TMDB_READ_ACCESS_TOKEN` environment variables were not set during this check; other credential locations were not inspected. Direct IMDb pages returned HTTP 403. A cached candidate can support a historical comparison but cannot prove that an entry remains present or is the correct current API result. We did not run an automated film resolver or obtain a human review-time measurement.

## Sample and time fields

Production year, the year of an observed screening, source publication year and a source's local-release eligibility year are different fields. `?` means not established from the cited evidence, not that the event did not occur. A Cannes competition year does **not**, by itself, prove a world-premiere year; a festival archive edition is not necessarily a page's publication year. No year below asserts US or other local theatrical-release eligibility unless expressly identified.

| Cohort / source title and format | Original source and observed edition | Production year | Earliest premiere year verified | Source publication year | Local-release eligibility |
| --- | --- | --- | --- | --- | --- |
| 2010–2019: *Lung Boonmee Raluek Chat* / *Uncle Boonmee Who Can Recall His Past Lives*, feature, Apichatpong Weerasethakul | Cannes film record `https://www.festival-cannes.com/en/f/lung-boonmee-raluek-chat/`, competition 2010 | 2010 | ? | ? | ? |
| 2010–2019: *Jodaeiye Nader az Simin* / *Nader and Simin, A Separation*, feature, Asghar Farhadi | [Berlinale programme](https://www.berlinale.de/external/programme/archive/pdf/20116885.pdf), competition 2011 | ? (programme labels film 2011) | ? | ? | ? |
| 2010–2019: *Leidi*, short, Simón Mesa Soto | Cannes film record `https://www.festival-cannes.com/f/leidi/` and awards announcement `https://www.festival-cannes.com/en/2014/all-the-67th-festival-de-cannes-awards/`, 2014 | 2014 | ? | 2014 (announcement) | ? |
| 2010–2019: *Manbiki Kazoku* / *Shoplifters*, feature, Hirokazu Kore-eda | Cannes film record `https://www.festival-cannes.com/en/f/manbiki-kazoku/`, competition 2018 | 2018 | ? | ? | ? |
| 2010–2019: *All These Creatures*, short, Charles Williams | Cannes film record `https://www.festival-cannes.com/en/f/all-these-creatures/`, competition 2018 | 2018 | ? | ? | ? |
| 2010–2019: *Portrait de la jeune fille en feu* / *Portrait of a Lady on Fire*, feature, Céline Sciamma | Cannes film record `https://www.festival-cannes.com/en/f/portrait-de-la-jeune-fille-en-feu/` and festival article `https://www.festival-cannes.com/en/2019/meet-the-team-from-portrait-de-la-jeune-fille-en-feu-portrait-of-a-lady-on-fire/`, 2019 | 2019 | ? | 2019 (article) | ? |
| 2020–2026: *Heojil Kyolshim* / *Decision to Leave*, feature, Park Chan-wook | Cannes film record `https://www.festival-cannes.com/en/f/heojil-kyolshim/` and selection announcement `https://www.festival-cannes.com/en/press/press-releases/the-films-of-the-official-selection-2022/`, 2022 | 2022 | ? | 2022 (announcement) | ? |
| 2020–2026: *Hai Bian Sheng Qi Yi Zuo Xuan Ya* / *The Water Murmurs*, short, Jianying Chen | Cannes film record `https://www.festival-cannes.com/en/f/hai-bian-sheng-qi-yi-zuo-xuan-ya/`, competition 2022 | 2022 | ? | ? | ? |
| 2020–2026: *No Other Land*, documentary, Basel Adra, Hamdan Ballal, Yuval Abraham and Rachel Szor | [Berlinale 2024 programme](https://www.berlinale.de/media/download/presse/dossier/pressedossier-2024.pdf), world premiere; Film Comment's [US-release list](https://www.filmcomment.com/best-films-of-2024/) and [undistributed list](https://www.filmcomment.com/best-undistributed-films-of-2024/) | ? (Berlinale programme labels film 2024) | 2024 (world premiere) | ? (poll pages do not state publication dates) | The same film appears on lists with apparently conflicting US-release and undistributed criteria. Preserve both observations; do not infer a US release date or resolve the inconsistency without further evidence. |
| 2020–2026: *The Man Who Could Not Remain Silent*, short, Nebojša Slijepčević | Cannes film record `https://www.festival-cannes.com/en/f/the-man-who-could-not-remain-silent/` and competition programme `https://www.festival-cannes.com/en/2024/the-short-film-competition-programme/`, 2024 | 2024 | ? | 2024 (programme) | ? |
| 2020–2026: *Percebes*, animated short, Alexandra Ramires and Laura Gonçalves | [Annecy award record](https://www.annecyfestival.com/about/archives%3Aen/2024%3Aen/award-winners/film-index%3Afilm-20242481), 2024 | 2024 | ? | ? | ? |
| 2020–2026: *Sheep in the Box*, feature, Hirokazu Kore-eda | Cannes film record `https://cinemadedemain.festival-cannes.com/en/f/sheep-in-the-box/` and selection announcement `https://www.festival-cannes.com/en/press/press-releases/the-films-of-the-official-selection-2026/`, 2026 | 2026 | ? | 2026 (announcement) | ? |
| Older retrospective: *Jeanne Dielman, 23, quai du Commerce, 1080 Bruxelles*, feature, Chantal Akerman | [Criterion's 2012 retrospective article](https://www.criterion.com/current/posts/2429-sight-sound-poll-2012-jeanne-dielman-23-quai-du-commerce-1080-bruxelles) is a derivative account of the Sight and Sound poll, not an additional independent critic ballot. | ? (article labels film 1975) | ? | 2012 | ? |
| Older retrospective: *Man with a Movie Camera*, documentary, Dziga Vertov | [Film at Lincoln Center staff retrospective](https://www.filmlinc.org/daily/film-at-lincoln-center-staff-share-top-10-of-2023-lists/), a 2023 viewing published in 2024 | ? (article labels film 1929) | ? | 2024 | ? |

## Identity lookup log

Statuses refer to what could be checked in this session: **verified** would require a current, accessible catalog result plus an independently supported work identity; **ambiguous** means conflicting evidence needs review; **unknown** includes inaccessible sources, stale snapshots and unattempted lookups. IMDb suggestions are not treated as confirmed IDs after the 403. Match original title, director, film type and additional context; year alone is insufficient.

Two further leads below come from indexed Wikidata pages, inspected on 2026-10-29; the reader labeled one snapshot about a month old and the other about a week old. Their page links supplied revision permalinks, which could not be separately fetched by the reader. Wikidata's [structured data is CC0](https://www.wikidata.org/wiki/Wikidata:Licensing), but both ID claims cite TMDB and an IMDb-ID-based inference retrieved in 2024. They are derivative leads, not independent confirmation of a TMDB match or a current catalog result. No source page bodies are retained.

| Film | TMDB / IMDb result as of the attempted check on 2026-10-29 | Reason and evidence |
| --- | --- | --- |
| *Uncle Boonmee Who Can Recall His Past Lives* | **Unknown, Wikidata candidate** | Indexed [Wikidata Q553901, revision 2537971460](https://www.wikidata.org/w/index.php?oldid=2537971460&title=Q553901) names the title and director and asserts TMDB 38368 and IMDb tt1588895. No current TMDB or IMDb lookup was made; retain the original title and director from Cannes. |
| *A Separation* | **Unknown, Wikidata candidate** | Indexed [Wikidata Q640561, revision 2559031347](https://www.wikidata.org/w/index.php?oldid=2559031347&title=Q640561) names the title and director and asserts TMDB 60243 and IMDb tt1832382. No current TMDB or IMDb lookup was made; preserve the festival's longer English and transliterated titles. |
| *Leidi* | **Unknown** | Catalog lookup not attempted; do not infer a missing catalog entry. |
| *Shoplifters* | **Unknown, cached candidate** | [TMDB 505192](https://www.themoviedb.org/movie/505192) snapshot matches title, director and 2018, and gives original title 万引き家族; current API identity has not been checked. |
| *All These Creatures* | **Unknown** | TMDB search was not accessible. [IMDb candidate tt8296622](https://www.imdb.com/title/tt8296622/) returned 403 on direct access; prior search-index evidence suggested a 14-minute duration versus Cannes's 13 minutes. A cached [IFFR 2019 record](https://iffr.com/en/iffr/2019/films/all-these-creatures) also lists Charles Williams, 2018 and 13 minutes. Verify the candidate and differing duration before acceptance. |
| *Portrait of a Lady on Fire* | **Unknown, cached candidate** | [TMDB 531428](https://www.themoviedb.org/movie/531428-portrait-de-la-jeune-fille-en-feu) snapshot matches the English and French titles and director; the current API has not been checked. |
| *Decision to Leave* | **Unknown, cached candidate** | [TMDB 705996](https://www.themoviedb.org/movie/705996) snapshot matches title and director and gives original title 헤어질 결심. Cannes's 2022 announcement and film page use different romanizations; retain both source spellings. |
| *The Water Murmurs* | **Unknown** | TMDB search was not accessible. [IMDb candidate tt19844654](https://www.imdb.com/title/tt19844654/) returned 403 on direct access; recheck the director and alias before accepting. |
| *No Other Land* | **Unknown, cached candidate** | [TMDB 1232493](https://www.themoviedb.org/movie/1232493) snapshot names the same four directors and gives original title لا أرض أخرى; no fresh API result was available. |
| *The Man Who Could Not Remain Silent* | **Ambiguous, cached candidate** | [TMDB 1279229](https://www.themoviedb.org/movie/1279229-covjek-koji-nije-mogao-sutjeti) snapshot gives original title Čovjek koji nije mogao šutjeti, labels the header 2025 but separately shows a 2024 release date, while Cannes records production 2024. The Cannes programme lists 13 minutes and its film page lists 14; verify date and runtime rather than discarding or silently selecting either. |
| *Percebes* | **Unknown** | Direct TMDB candidate search was inaccessible. [IMDb candidate tt32342056](https://www.imdb.com/title/tt32342056/) returned 403. Annecy's film record lists both directors and 11:25; an indexed [Portuguese Short Film Agency record](https://agencia.curtas.pt/filmes/show/579) lists both directors and 11:30. The agency page timed out on direct retrieval; preserve the five-second disagreement and recheck the candidate and format. |
| *Sheep in the Box* | **Unknown** | Catalog lookup not attempted. The 2026 selection is not evidence that the film is already present in a particular catalog. |
| *Jeanne Dielman* | **Ambiguous, cached candidate** | [TMDB 44012](https://www.themoviedb.org/movie/44012-jeanne-dielman-23-quai-du-commerce-1080-bruxelles) snapshot labels the header 1976; the cited retrospective describes the film as 1975. Retain the discrepancy and review the dated events. |
| *Man with a Movie Camera* | **Unknown, cached candidate** | [TMDB 26317](https://www.themoviedb.org/movie/26317) snapshot matches title, year and director and gives original title Человек с киноаппаратом; not a current API observation. |

## Next measurements and priorities

1. Prioritize independently sampled festival shorts and non-English/translated-title sources, then older retrospective appearances. Expand documentary and animation separately; this convenience sample overrepresents Cannes and cannot establish broad geographic or temporal coverage.
2. Freeze a rights-permitted, stratified source sample and a separate audited answer key. Record exact source edition and locator, raw and translated titles, director, format, country, production year, verified premiere date, publication date and source-specific eligibility separately. Reconcile taxonomy and overlaps with B1 before any cross-source comparison.
3. Against an authorized, version-recorded TMDB API, record every attempt, response outcome and candidate set. A timeout, 403, partial or failed search is **unknown**, never a missing-catalog film. Log optional IMDb evidence only where independently accessible and permitted.
4. Have a reviewer time actual independent adjudication and resolve candidate identities without seeing automatic acceptance decisions. For each stratum report denominators, automated acceptance coverage, precision among independently reviewed accepted matches, unresolved rate, and only **confirmed** absent-catalog rate. Report elapsed human review time and its sample size; none has yet been measured.
5. Do not advance a source-expansion or identity-accuracy claim from this preliminary list. Real current catalog measurements, reviewed decisions, permissions and reproducible error handling remain open.

## Runnable candidate-search experiment

`sample.json` freezes the fourteen source-linked cases above as factual query
inputs, including aliases, directors, source edition and unresolved year or
eligibility conflicts. Every accepted ID remains null. It contains no captured
publisher page bodies and does not establish catalog matches.

From this worktree root, a credential-free dry run makes zero requests:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
  uv run --no-sync python -m docs.research.history.run \
  --output .cache/history-dry-run.json
```

For an authorized live run, configure `TMDB_READ_ACCESS_TOKEN` or `TMDB_API_KEY` locally, review
the applicable provider terms and retention period, and supply an explicit
retention note. Use a new observation filename each time:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
  uv run --no-sync python -m docs.research.history.run --live \
  --retention-note 'Record the verified provider plan, use and retention basis here' \
  --output .cache/history-observation-01.json
```

The [official movie-search endpoint](https://developer.themoviedb.org/reference/search-movie)
searches original, translated and alternative titles. The runner uses one
recorded query per film, English response language and `include_adult=false`;
it deliberately applies no disputed release-year filter. Search results do not
include director verification. Additional alias queries and film/credits
adjudication are separate reviewed work, not automatic acceptance. Authentication
uses the documented [Bearer header or v3 API key](https://developer.themoviedb.org/docs/authentication-application).
The Bearer token takes precedence when both are configured. A v3 key is sent only
in the HTTPS request's `api_key` query parameter; evidence records use the fixed
credential-free endpoint and never retain authenticated request URLs or exception
messages. Neither credential is written into observation files.

Each observation records exact query parameters, per-page UTC attempt time,
HTTP status, exposed rate-limit headers, response hash, request count and selected
candidate metadata. No raw payloads or credentials are retained. Monetary cost
is unknown. Failed observations retain a bounded processing phase and exception
class, without exception messages; validated page/result totals distinguish
budget and pagination failures from transport, HTTP, decoding or schema failures.
Human review time
remains unmeasured. `--max-pages` defaults to five per
query (at most 70 requests for fourteen cases); an exceeded budget, changed page
counts, duplicate IDs, truncated JSON, incomplete total or failed page leaves
the search unknown. Partial candidates remain only in their page-attempt
evidence. No retries are made. An empty successful search still cannot establish
catalog absence or a film match. All identities require independent review.

Outputs are restricted to this worktree's ignored `.cache` directory, and an
existing file is never overwritten. Local storage is not an exemption from
provider expiry/deletion rules: the operator must apply the verified retention
basis to these bounded observations. The runner does not claim that a free-text
note grants rights. Optional IMDb verification remains outside this experiment.

Offline tests cover successful pagination, missing credentials, empty results,
request failure, malformed/truncated data, changing totals, duplicate IDs,
page-budget exhaustion and partial later-page failures. This enables a future
reproducible measurement. At initial preparation, no live TMDB requests, current
precision or coverage results had been obtained; see the dated continuation above
for the later observations and remaining acceptance gaps.
