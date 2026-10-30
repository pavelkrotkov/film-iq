# B4 paired provider observation — 2026-10-30

Part of issue #14. Protocol frozen before the bulk acquisition below. This
continues the same sixty-film convenience cohort and source-work audit; it does
not replace missing titles or accept Gate B. A separate one-film native-key/
catalog probe returned HTTP 200 and matching Avengers: Endgame metadata.

## Fixed protocol

- Reuse the original 60 keys, strata and source-work evidence. The accepted TMDB
  manifest remains the identity basis. IMDb identifiers asserted by TMDB seed
  Movie of the Night catalog requests; they are not independently verified IMDb
  truth. A separate reviewer must check returned work metadata and both ID fields
  before corresponding offers enter verified comparisons. Unresolved work IDs
  remain unknown in the original denominator.
- For each film, make one current TMDB US provider request and one native Movie
  of the Night show request with `country=us`, recording UTC boundaries, HTTP
  status, quota headers, response hashes and selected factual metadata. No retries.
  This is 60 requests per provider, plus the separate native probe and a bounded
  provider-label lookup if needed. HTTP, decoding, schema and missing-country
  failures remain unknown; never infer absence or removals.
- Keep raw response bodies, images, credentials, synopses and catalog dumps out
  of Git. Retain only selected project-local factual observations in ignored
  cache. Published results are aggregates with receipt hashes and attribution.
  Native storage and applicable-use conditions are documented in the adjacent
  rights report; this provider comparison is not an AI-model training or
  extraction-model evaluation experiment. TMDB historical-retention rights
  remain unresolved and are not granted by a free-text note.
- Reuse existing conservative normalizers. Preserve service IDs, original access
  types, add-on IDs, quality variants, prices and asserted availability dates.
  Provider-specific row counts have different granularity. A separately reviewed
  brand crosswalk may describe common film/service/type observations; unknown
  mappings, ad tiers and account entitlements must not be forced into agreement.
  Nominal overlap is not independently verified provider accuracy.
- Check first-party links for the fixed examples Nimona, Inside Out 2, No Other
  Land and Perfectly a Strangeness where a provider returns one. Public title
  presence, a transaction control and an authenticated entitlement are distinct
  evidence. No purchases, playback/account changes or watchlist writes.
- Compare on the same UTC date with actual per-request timestamps. This new
  paired pass and the earlier TMDB pass are all observation date one. Two later
  genuinely separated dates are still required. Preserve earlier outputs.

## Results — same observation date, not Gate B acceptance

The native Movie of the Night key worked. All 120 paired requests returned HTTP
200 during **2026-10-30 12:53:42.210692–12:54:06.199569 UTC**. TMDB supplied
53 explicit usable US responses; native Movie of the Night supplied 49. Missing
country data remains unknown even after HTTP 200. Neither source supplied an
explicit complete-empty response. All sixty work lookups passed the separate
automated identity review; this is work-level support, not human precision,
IMDb-site verification, reconciled release dates or exact-cut identity. The
audit preserves six native/source year-context differences, 26 runtime
differences and seven missing/unusable native runtimes without resolving cuts
or declaring which source is correct.

| Assigned stratum (10 works each) | TMDB complete / unknown | Native complete / unknown |
| --- | ---: | ---: |
| Mainstream | 10 / 0 | 10 / 0 |
| International arthouse | 10 / 0 | 9 / 1 |
| Older | 10 / 0 | 9 / 1 |
| Documentary features | 10 / 0 | 10 / 0 |
| Animated features | 10 / 0 | 10 / 0 |
| Shorts / experimental | 3 / 7 | 1 / 9 |

The raw units differ: TMDB's **529** service/category rows contain 81 flatrate,
218 rent, 204 buy, eight ads and eighteen free assertions. Native's **274**
offer rows, including quality variants, contain 45 subscription, 79 rent, 93 buy, four free and 53
add-on assertions. These totals cannot establish comparative offer coverage.
Local selected records retain source IDs/categories, quality, prices and
provider-asserted dates; original HTTP response hashes are preserved separately from
selected-payload normalization. Failed normalization produces no partial offers.

### Bounded nominal comparison

An explicit manual crosswalk maps **237/529 TMDB source units**, leaving **292
unmapped**, versus **274/274 native variants**. This asymmetry is material:
source-only mapped tuples can correspond to unmapped units in the other source.
Within the **49 jointly complete films**, the TMDB denominator is 524 source
units, of which 236 map and 288 remain unmapped. Deduplicating only mapped
film/platform/nominal-access/add-on tuples yields 231 TMDB tuples and 226 native
tuples: **180 common, 51 TMDB-only and 46 native-only**. These are differences
between mapped assertions, not independently confirmed source exclusivity,
absence, errors, provider accuracy or superiority.

TMDB Amazon/Apple/Roku channel subscriptions map to a host plus add-on brand,
never the host's base subscription. Native `service.id` identifies the host and
`addon.id` the target; standalone MUBI differs from MUBI through Prime. Amazon
Video 10 maps to native Prime rent/buy and Apple TV Store 2 to native Apple
transactions. Netflix's separate standard/ad IDs and Paramount Premium/Essential
IDs collapse only for this nominal brand analysis; native unspecified plans do
not prove exact-tier agreement. Free and ads remain distinct: Tubi's three
TMDB ads assertions differ from native free classifications. No library
eligibility is inferred. Unmapped IDs and all source rows remain local only.

### Public spot checks and pre-subscription discovery

Public title pages are benchmark spot checks, **not prerequisites for routine
API discovery**. Consumer login or subscription is not required to discover
advertised films. Personal entitlement stays unknown by design; public plan
qualifiers can inform discovery before purchase without inspecting an account.

Signed-out browser checks found [Nimona on Netflix](https://www.netflix.com/title/81444554),
[Inside Out 2 on Disney+](https://www.disneyplus.com/browse/entity-ec9f9fa3-fbae-4a25-b722-12c3b8ab0ef4)
and [Perfectly a Strangeness on Criterion](https://www.criterionchannel.com/films/3ICjW08N/perfectly-a-strangeness).
They establish public platform/work presence and visible controls, not playback
or title-specific ad-tier access. Netflix's web-reader EUR versus browser USD
marketing illustrates locale uncertainty. For Inside Out 2, TMDB asserted Apple
rent/buy while native returned Disney and Prime offers; this difference is not a
verified Apple absence. Perfectly a Strangeness has a TMDB **Kanopy free** row
and a native Criterion subscription row. [Kanopy library access](https://help.kanopy.com/en-us/4171.htm)
requires a participating library; collection eligibility remains unknown. A Plex
aggregation page listing third parties is not first-party Kanopy evidence.

The [public US Apple SKU lookup](https://itunes.apple.com/lookup?id=1840776517&country=us)
returned one No Other Land movie record matching native Apple SKU 1840776517.
Using `Decimal(str(value))`, HD buy **USD 9.99**, SD buy **USD 7.99**, and HD
rent **USD 4.99** match corresponding native assertions. This is SKU metadata
agreement, not checkout, account ownership or exact-cut proof. Apple's runtime
is about 95.87 minutes versus native 92; that discrepancy remains unresolved.
No purchase, playback, login or consumer-account change was attempted.

A separate user-selected **Peacock discovery supplement** made one native
`/shows/search/filters` request with `country=us`,
`catalogs=peacock.subscription` and `show_type=movie`. All **20 returned shows**
had a Peacock subscription assertion, including The Host (2006), Train to Busan
(2016) and The Man from Nowhere (2010). **`hasMore=true`**: all first-page rows
were retained, but later pages were not fetched; this is not a complete catalog.
The provider's [published API schema](https://github.com/movieofthenight/streaming-availability-api/blob/e68fa1bad45d09f9afae1ed3e06884ffe338f76d/openapi.yaml)
already exposes the service, access type, add-on, deep link, quality, price and
availability-date fields. Discovery should use these API fields directly. The
streaming-option schema's generic subscription label does not identify an exact
Peacock plan or guarantee ad-free access. `availableSince` is provider detection
time, not independently verified launch time; `expiresOn` is a supplied last-day
assertion when present. These candidates received no independent work/offer
accuracy audit. The result
is outside the frozen sixty-film overlap/accuracy denominator. Zero Peacock
assertions in that cohort is not proof of no Peacock availability.

Separately, Peacock's [public movie catalog](https://www.peacocktv.com/stream/movies)
and [Disclosure Day page](https://www.peacocktv.com/stream-movies/disclosure-day)
advertise Disclosure Day (2026) as streaming now. This film was not claimed to
appear in the API's first page. The [official tier table](https://www.peacocktv.com/help/article/select-tier)
includes movies with Premium and Premium Plus and excludes them from Select.
Premium has ads; Premium Plus has limited exceptions, including some movies.
Disclosure Day's particular exception status is unknown. These three pages were
read publicly; web-reader crawl labels were today/today/four days ago, not
independent live-origin timestamps. Public discovery needs no consumer login;
no paid-plan recommendation follows.

### Requests, reproducibility and remaining evidence

The paired pass used **60 TMDB + 60 native requests**; the separate native key/
catalog probe adds one, giving **121 provider requests** for that fixed phase.
The Peacock supplement adds one native request: this continuation totals **62
native + 60 TMDB = 122 provider requests**. Apple's one public HTTP lookup makes
**123 counted study data requests**, excluding documentation lookups and
unmetered web-reader/browser navigation and assets. The earlier 225 TMDB requests remain separate. No quota
headers were returned in the paired pass, native probe or Peacock request;
actual allowance, account plan, monetary charges and human labor are unknown.
Paired request start skew ranged **0.149584–0.346159 seconds**, mean 0.17907455.
The final request body-read ended 12:54:06.069131 UTC; the capture finish includes
subsequent local processing. Fetch timers exclude normalization and pacing.

The original accepted TMDB manifest stays unchanged. A new local accepted
both-ID manifest links it to the independent native work audit and is the stable
input for the two later dates; it is distinct from the pre-audit capture seed.
The paired CLI dry run retained 120 observations and made zero requests.
The ignored cache helper uses the existing normalizers directly and makes no
HTTP calls. Selected factual artifacts remain local; the following hashes are
file receipts, not redistributed catalog data or hashes of reserialized bodies.

| Local artifact | SHA-256 |
| --- | --- |
| `paired-capture-20261030.json` | `c029944dd6d658701327e74d0841581dce1cfe64a951403a763074d5a9632ea4` |
| `paired-seed-manifest-20261030.json` | `7944a75420068c76fe6d893da9eca31125a5f157a06e801844d81ede4813244b` |
| `independent-identity-audit-20261030.json` | `3c7f6422ca7ccb5261545e234876c396c6a219da61315c7d1b8f0dfcf561fbcc` |
| `accepted-paired-manifest-20261030.json` | `303cd59ff2996571492a7aaee032c26fd7552673e234951295c625a515a0aa12` |
| `comparison-summary.json` | `b66b6606de308c830f8ad93f600a0e4071f755b30fb712e7c2787ba726ab8587` |
| `comparison-crosswalk.json` | `4a3e3ee358a34d18f079bf40f7da27cc9e8ce9c3ed3f15bac59695e1740bc7d1` |
| `comparison-normalized-observations.json` | `7632acc4b7d8baba2f0c08ecb58fc67869329d077785107a63975fb3f99ebbfa` |
| `apple-store-check-20261030.json` | `5ab511651684aeca857ea20bde53e865ec7b6260802cee3c6b69913d695ec62b` |
| `paired-first-party-checks-20261030.json` | `cfd779aa2195bdbfd26b23b656a34dcc31eb6c47640433897d27cdad2f6827f8` |
| `peacock-api-discovery-20261030.json` | `d7d8ee89db8bae4647c9a9d25bf263c6a39241a45ce92e673e6d237f6ddc4026` |
| `peacock-public-check-20261030.json` | `d3ee052d197f0db51c4a162685deb3915174083967d38f6582306e9f02ca8aa3` |

All captures are **observation date one, 2026-10-30 UTC**. Two genuinely later
dates, change/expiry timeliness measurements and unresolved rights/plan-specific
classification evidence remain. Personal account entitlement remains unknown; it is not a public discovery
gate. Public plan/region qualifications are reported before subscription. No human precision,
provider superiority, polling cadence or Gate B acceptance is claimed. B4 #14,
B8 #18 and ADR 0008 remain open/provisional.

Streaming availability information is provided by [Streaming Availability API by Movie of the Night](https://www.movieofthenight.com/about/api).
TMDB observations use JustWatch data via TMDB. This product uses the TMDB API but is not endorsed
or certified by TMDB. The [rights ledger](rights-20261030.md) preserves native
attribution/storage/third-party-use conditions and unresolved TMDB archival
rights. This is a provider comparison, not AI-model training or extraction-model
evaluation under native terms §10. No response bodies, credentials, images,
synopses, row-level crosswalk or catalog dump are committed.
