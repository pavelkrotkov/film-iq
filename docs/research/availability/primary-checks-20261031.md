# B4: bounded first-party corroboration of date-two changes

Related [B4 #14](https://github.com/pavelkrotkov/film-iq/issues/14) and
[C4 #22](https://github.com/pavelkrotkov/film-iq/issues/22). The
[date-two comparison](comparison-20261031.md) found nine newly reported and two
no-longer-reported source opportunities across five films. These signed-out
checks follow those exact source links; they are current corroboration, not
historical change timing, purchase advice or a provider selection.

## Apple SKU metadata checks

The original Apple TV pages for Wild Diamond and Sugarcane were inaccessible
through the web reader at 15:14 UTC; it exposed no HTTP status. One fallback per
film queried Apple's public US SKU metadata endpoint, using the SKU already in
the source locator. Both returned HTTP 200 and one matching title/director record
at **2026-10-31 15:14:58 UTC**.

| Work / first-party SKU | Native date-two assertions corroborated by current Apple metadata |
| --- | --- |
| [Wild Diamond — 1823301255](https://itunes.apple.com/lookup?id=1823301255&country=us) | HD buy USD14.99; SD buy USD12.99; HD rent USD4.99 |
| [Sugarcane — 1796301439](https://itunes.apple.com/lookup?id=1796301439&country=us) | HD buy USD14.99; HD rent USD3.99 |

Prices were parsed with `Decimal(str(value))` into USD minor units. Purchase and
rental fields remain distinct, as do HD and SD; no generic service fee or billing
interval is inferred. This is SKU metadata agreement, not checkout, playback,
account ownership, tax treatment or exact-cut proof. Apple exposed no departure
or independently verified effective-addition date in these selected fields.
Missing expiry stays unknown and cannot verify a future dated plan.

The bounded packet also assigns Viet and Nam, Vertigo and Inside Out 2 to an
independent check. Their results are pending this draft; no success is inferred.

## Request and retention scope

This pair used **two public-page tool attempts plus two public SKU HTTP lookups**,
within the four-attempt budget. The page tool did not expose underlying HTTP or
asset counts, so four is an application-level attempt count. No streaming-provider
API, polling job, sign-in, playback or purchase was used. No page body is retained;
private receipts contain minimal factual fields, locator, time and access failures.
Original provider captures remain unchanged. Existing rights/retention limits and
the Nov1 third-date/final B4/B8 gates remain in force. Current agreement alone
cannot measure source-change correctness historically or detection latency.

Streaming availability information is provided by
[Streaming Availability API by Movie of the Night](https://www.movieofthenight.com/about/api).
