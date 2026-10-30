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

## Results

Acquisition, independent work-ID review and first-party checks are in progress.
