# B4: second dated observation, 2026-10-31

Related [B4 #14](https://github.com/pavelkrotkov/film-iq/issues/14) and
[C4 #22](https://github.com/pavelkrotkov/film-iq/issues/22). This records date two,
not the final three-date benchmark, provider selection or production adoption.
The [date-one report](comparison-20261030.md), [rights ledger](rights-20261030.md)
and [remaining-run protocol](dated-observations.md) retain their scope.

## Executed observation

At the read-only inspection on **2026-10-31 at 14:58 UTC**, the existing Oct31
launchd job was not running, with **one run and exit code 0**. Its stdout reported
60 candidates, 120 observations and 120 requests; stderr was empty. The result
contains exactly one observation per accepted film/provider pair. The manifest
hash matches the frozen accepted 60-film both-ID cohort; no cohort expansion or
extra discovery request was made by this pass.

| Provider | UTC observation timestamp range | Requests / HTTP 200 | Complete US responses | Unknown | Source offer rows: Oct30 → Oct31 |
| --- | --- | ---: | ---: | ---: | ---: |
| TMDB / JustWatch | 14:00:00.238122–14:00:11.633715 | 60 / 60 | 53 | 7 | 529 → 529 |
| Movie of the Night native | 14:00:00.386625–14:00:11.707326 | 60 / 60 | 49 | 11 | 274 → 284 |

All responses were HTTP 200, but missing usable US data still remains unknown.
No quota headers were reported. A successful request does not establish remaining
allowance, account plan, charges or unlimited use. The source-row granularities
differ: native rows can represent quality/price variants; raw row counts do not
measure comparable coverage or independent opportunities across providers.
Corresponding film/provider requests were approximately 25h06m apart from date
one (90,365.7–90,378.1 seconds), so this is a genuinely later observation date.

## Bounded within-source comparison

Only pairs complete on both dates were compared: **53 TMDB pairs and 49 native
pairs**. Unknown observations never supply negative evidence.

- TMDB: no differences in source-native `(type, service, add-on)` sets or the
  selected detailed offer multisets.
- Native: **five film keys** have different source-native opportunity sets,
  with **nine newly present and two no-longer-present source opportunities**.
  These counts deduplicate type/service/add-on within each film and source;
  they are source assertions, not verified global arrivals/removals.
- Native: **12 film keys** have different detailed offer multisets, including
  opportunity differences and supplied price/quality/date/locator differences.
  This is a broader comparison, not 12 additional changed films or 12 verified
  price changes. The net ten-row increase uses quality/price-variant row units;
  it must not be equated with the net seven opportunity-set increase.

The detailed comparison retains the multiset of type, service, add-on, locator
and the original `source_details` (price, quality, supplied addition/expiry fields).
It does not flatten variant prices or turn detection time into effective addition.
Original captures and all source details remain unchanged in the private cache;
no offer dump or row-level catalog is published here.

At the capture inspection there was no independently timed first-party change check.
The subsequent [bounded primary checks](#bounded-first-party-follow-up--2026-10-31) distinguish
current SKU corroboration from unknown historical effective times.
The actual transition times, correctness of the source differences, false-removal
rate and change-detection latency therefore remain **unknown**, not zero. Earlier
bounded first-party checks remain dated date-one evidence. Personal account/tier
entitlement and exact-cut qualifications remain unknown where untested.

## Bounded first-party follow-up — 2026-10-31

The five changed-film source locators guide this signed-out follow-up, not a new
provider search. The original Apple TV pages for Wild Diamond and Sugarcane were
inaccessible through the web reader at 15:14 UTC, with no HTTP status exposed.
One fallback per film used Apple's public US SKU metadata endpoint and the SKU
already in the provider locator. Both returned HTTP 200 and one matching title/
director record during **2026-10-31 15:14:57–15:14:58 UTC**.

| Work / first-party SKU | Native date-two transaction assertions corroborated by current Apple metadata |
| --- | --- |
| [Wild Diamond — 1823301255](https://itunes.apple.com/lookup?id=1823301255&country=us) | HD buy USD 14.99; SD buy USD 12.99; HD rent USD 4.99 |
| [Sugarcane — 1796301439](https://itunes.apple.com/lookup?id=1796301439&country=us) | HD buy USD 14.99; HD rent USD 3.99 |
| [Việt and Nam — 1805009787](https://itunes.apple.com/lookup?id=1805009787&country=us) | HD buy USD 14.99; SD buy USD 12.99; HD rent USD 4.99 |
| [Inside Out 2 — 1757560069](https://itunes.apple.com/lookup?id=1757560069&country=us) | HD buy USD 19.99; HD rent USD 3.99 |

Prices use `Decimal(str(value))` into USD minor units. HD/SD and rent/buy remain
separate. This is current SKU metadata agreement, not checkout, playback, account
ownership, tax treatment or exact-cut proof. No departure or independently timed
effective-addition date is established. Missing expiry remains unknown and cannot
verify a future dated plan.

This pair used two public-page tool attempts plus two public SKU HTTP lookups,
within its four-attempt budget. The page tool exposes no underlying HTTP/asset
counts, so four is an application-level attempt count. No page body is retained;
minimal factual receipts record locators, times, fields and access failures.
No streaming-provider API, polling job, sign-in, playback or purchase was used.

An independent reviewer checked the remaining three films during **15:17:13–
15:17:16 UTC**, with six signed-out HTTP GETs, redirects disabled and no retries.
Apple TV pages for Việt and Nam and Inside Out 2 returned HTTP 200 with matching
title metadata; one US SKU lookup each returned a single matching title/director
record and the additional prices above. The Việt and Nam page metadata did not
establish the identity, tier or entitlement of the newly reported add-on
`tvs.sbd.1000249`; it remains unknown.

For [Vertigo's original Amazon locator](https://www.amazon.com/gp/video/detail/0IIILF2NQBCK5L54JUKV6ZD4I6),
the response was HTTP 302 and was not followed. A single
[same-ID Prime Video fallback](https://www.primevideo.com/detail/0IIILF2NQBCK5L54JUKV6ZD4I6)
returned HTTP 200 but no usable title/offer metadata in the bounded extraction.
Neither result verifies US buy/rent absence. The two no-longer-reported native
opportunities remain uncorroborated, not false removals or confirmed removals.

Across the four Apple works, current metadata corroborates **eight transaction
opportunities / ten native quality-price variants**. The ninth newly reported
opportunity is the unverified add-on. Historical effective times, source-change
accuracy and detection latency remain unknown for all cases. Total follow-up
budget consumed: **eight explicit public HTTP GETs plus two opaque web-reader
page attempts**, ten application-level attempts; underlying web-reader HTTP/asset
counts remain unavailable. No further request followed exhaustion of the budget.

## Receipts and remaining gate

| Private artifact | SHA-256 |
| --- | --- |
| Accepted paired manifest | `303cd59ff2996571492a7aaee032c26fd7552673e234951295c625a515a0aa12` |
| `paired-2026-10-31.json` | `56750c246f23354aba6c9287048d6854c2874279657b8b24be6b248ee1d4eaf1` |
| Date-one normalized observations | `7632acc4b7d8baba2f0c08ecb58fc67869329d077785107a63975fb3f99ebbfa` |

The Nov1 job was not running with **zero runs**; its result file did not exist
at inspection. It remains scheduled for **2026-11-01 10:00 America/New_York
(15:00 UTC)** across the DST change. No job was started, stopped or changed.
After the actual third date, compare complete pairs, investigate concrete source
differences with bounded first-party evidence, and publish a reviewed B4/B8
provider/rights decision, including inconclusive or no-go outcomes where warranted.
A winner, exact-tier entitlement, polling cadence and production retention/use
are not established by this second capture. Human review throughput is not a
new blocker for these provider observations; it belongs to any later bulk-work
estimate. No new account action or consumer sign-in is required for discovery.

Streaming availability information is provided by
[Streaming Availability API by Movie of the Night](https://www.movieofthenight.com/about/api).
TMDB observations use JustWatch data via TMDB. This product uses the TMDB API
but is not endorsed or certified by TMDB. The existing private study terms and
2027-04-30 TMDB refresh/deletion deadline remain unchanged; this report grants
no additional retention or AI/commercial-use permission.
