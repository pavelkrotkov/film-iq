# C2 bounded source coverage — 2026-10-31

This offline audit at main `0a7ac42` describes the selected, independently reviewed manual sample for [C2 #20](https://github.com/pavelkrotkov/film-iq/issues/20). It contains **114 accepted source observations across 24 cohorts**, with **112 resolved mentions representing 106 distinct reviewed works** and **two unresolved entries**. Observation counts are not independent critic counts or a general identity-precision estimate. C2 remains open.

The audit reused accepted typed components, reviewed catalog facts and retained source/identity audit receipts. It compared input hashes and current-component semantics before and after read-only inspection. There was no new source acquisition, personal-data access or change to the evidence database. Private receipts retain source references and metadata attribution; this report publishes aggregates only.

## Selected source scopes

| Evidence | Selected scope | Cohorts | Observations |
| --- | --- | ---: | ---: |
| Individual critic selections | Senses of Cinema: Luke Aspell 2018; Julien Allen, Michael J. Anderson and Dan Auiler 2023; Marcelo Alderete 2024 | 5 | 47 |
| Preservation selections | Library of Congress National Film Registry: complete 25-entry editions for 2020 and 2022 | 2 | 50 |
| Festival awards | Sixteen date-qualified Wikidata film Palme d’Or statements, each corroborated against primary records: 2010–2019 and 2021–2026 | 16 | 16 |
| Historical performance award | One Library of Congress-reported Best Actor prize; ceremony edition and day unknown | 1 | 1 |

The five contributor scopes are complete within their selected ballots, with 7, 10, 10, 10 and 10 entries respectively. They remain `intentionally_partial` in publisher coverage: other ballots and sections were not inspected. Only the two Registry cohorts are encoded `complete`; the seventeen award contexts remain intentionally partial. Seven source-policy IDs span three publication/transport families. All 24 manifests attest allowed use for their declared scopes through manual curated CSV input; this is not permission for a broader crawl, reuse method or bulk backfill.

Critic ballot years contain 7 observations for 2018, 30 for 2023 and 10 for 2024. Registry editions identify preservation-selection years, not film-release years. Award editions identify award years; year-only precision remains year-only, with no invented January 1 effective date. The undated ceremony for the historical performance prize stays unknown. The Palme query excludes undated claims, so its missing 2020 row proves neither source absence nor complete festival coverage.

The 47 critic observations retain verified original lineage in normalized legacy fields. For the **67 noncritic observations**, normalized legacy `lineage_kind` and `lineage_verification` remain **unknown**. Their independently reviewed typed classifications and descriptive primary/derivative lineage audits are retained separately: Registry selection and derivative award reporting must not be presented as extra critic votes. This audit does not silently retag generic metadata; any correction needs a versioned review history.

## Reviewed catalog release years

Catalog release dates are available for all 106 reviewed works and span 50 distinct year labels, from 1898 to 2026. These are catalog assertions, separate from source-listed dates, production dates and eligibility. The two unresolved source entries are outside this work-level denominator.

| Catalog release year | Distinct reviewed works |
| --- | ---: |
| 2010 | 2 |
| 2011 | 2 |
| 2012 | 1 |
| 2013 | 1 |
| 2014 | 1 |
| 2015 | 1 |
| 2016 | 1 |
| 2017 | 1 |
| 2018 | 7 |
| 2019 | 1 |
| 2020 | 0 |
| 2021 | 1 |
| 2022 | 2 |
| 2023 | 23 |
| 2024 | 9 |
| 2025 | 5 |
| 2026 | 1 |
| **2010–2026 subtotal** | **59** |

| Older catalog release group | Distinct reviewed works |
| --- | ---: |
| Before1900 | 1 |
| 1900–1949 | 6 |
| 1950–1969 | 9 |
| 1970–1989 | 20 |
| 1990–2009 | 11 |
| **Before 2010 subtotal** | **47** |

The zero for 2020 describes this sample only. Presence in sixteen of these seventeen release years does not establish source coverage for those years.

## Production-country and original-language coverage

**Only 42 of 106 works have these retained catalog fields; 64 remain uncollected and unknown for both dimensions.** Multi-country works contribute once to each recorded country, so the 83 work-country assertions across 27 labels are nonexclusive and do not sum to 42. Registry American-made eligibility does not fill a production-country field.

| TMDB production-country code | Works with that assertion |
| --- | ---: |
| AR | 3 |
| AT | 1 |
| BE | 2 |
| CA | 1 |
| CH | 3 |
| DE | 8 |
| DO | 1 |
| ES | 3 |
| FI | 2 |
| FR | 15 |
| GB | 7 |
| HU | 1 |
| IR | 3 |
| IT | 1 |
| JP | 2 |
| KR | 2 |
| MX | 1 |
| NA | 1 |
| NL | 3 |
| PL | 1 |
| PT | 1 |
| SE | 1 |
| SG | 1 |
| TR | 1 |
| TW | 1 |
| US | 16 |
| VN | 1 |

The twelve original-language labels below cover the same 42 works. Original language does not mean all spoken languages, subtitle availability or translated-source coverage.

| TMDB original-language code | Works |
| --- | ---: |
| de | 2 |
| en | 19 |
| es | 4 |
| fa | 1 |
| fi | 2 |
| fr | 7 |
| ja | 2 |
| ko | 1 |
| th | 1 |
| tr | 1 |
| vi | 1 |
| zh | 1 |

These bounded provider assertions use the TMDB API and are not endorsed or certified by TMDB. The retained metadata and derivatives carry the original 2027-04-29 expiry; they are not verified geography or language distributions for the other 64 works.

## Explicit format evidence

| Retained explicit primary-source label | Reviewed works |
| --- | ---: |
| Feature film | 17 |
| Short | 2 |
| Documentary form | 4 |

These labels cover 23 distinct reviewed works; **83 lack an explicit retained format classification**. Labels need not be mutually exclusive: documentary form is not a feature-versus-short duration class. Counts use explicit primary festival/archive classifications and retained factual identity-review assertions, never a genre or runtime threshold. One unresolved entry is explicitly a home-movie collection; the other unresolved entry has unknown format. No film ID or single release year was substituted for the collection.

## Review and failure evidence

All 114 accepted observations have explicit classification review. There are 112 reviewed identity mentions, two unresolved entries (one critic selection and one Registry collection), and one explicitly rejected same-title candidate in the 2020 Registry audit. These are bounded review outcomes, not a claim of general matching accuracy.

| Retained agent/API campaign | Recorded requests |
| --- | ---: |
| Additional 2023 critic identity review | 135 |
| 2018/2024 critic identity review | 37 |
| 2020 Registry details | 26 |
| 2022 Registry details | 24 |
| Palme supplied-ID details with credits | 16 |

The table is a nonexhaustive request inventory, not a total end-to-end cost or human effort measure. Separate Registry search receipts record 24 and 25 initial requests and two targeted requests. Each initial campaign retains twelve candidate windows smaller than its reported result count; neither retained window nor a successful chosen match proves exhaustive search. A separate critic identity query stopped at three pages/60 retained results and remained explicitly partial; an official festival record supported its final identity.

Source-access hurdles include a direct 2020 Registry reader returning 403, five historical Palme retrospective paths returning 403/timeouts, and a 2026 ceremony page returning 403. The audits used accessible primary alternatives and did not turn failed access into negative source facts. A complete transport-failure denominator is **unknown**. The historical B3 frozen layout-completeness result remains **3/8 held-out documents**; it is not the outcome rate of these manually curated cohorts or evidence for unattended extraction.

All 24 unchanged imports replayed without new semantic evidence; existing critic values and historical snapshots were preserved and typed snapshot replay was idempotent. This proves replay for these selected inputs, not arbitrary backfill layouts. **Representative human reviewer minutes and throughput remain unmeasured**; agent/API requests and elapsed time cannot substitute for them.

## Remaining acceptance boundary

Source-specific final Gate B decisions and any broader method/retention or bulk expansion approval remain open. So do representative human review measurements and broader geography/language/format coverage. The [Gate B research](gate-b.md), [C2 issue](https://github.com/pavelkrotkov/film-iq/issues/20) and authoritative [plan](../../plan.md) retain those gates. This bounded report establishes neither complete 2010–2026 coverage, calibration, predictive lift nor user satisfaction.
