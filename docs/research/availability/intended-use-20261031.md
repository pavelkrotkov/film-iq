# Provider intended use and candidate operating limits — 2026-10-31

This assessment narrows the remaining non-date questions for [B4 #14](https://github.com/pavelkrotkov/film-iq/issues/14), [B8 #18](https://github.com/pavelkrotkov/film-iq/issues/18), [C4 #22](https://github.com/pavelkrotkov/film-iq/issues/22) and [C8 #26](https://github.com/pavelkrotkov/film-iq/issues/26). It selects no provider, polling cadence, paid plan or production policy. The genuine third observation and reviewed B8 decision remain required.

## Declared product and current primary evidence

The release is a deterministic, self-hosted private companion. Personal ratings and plans are optional; no runtime personal model, ML feature, chatbot, public data API or standalone provider-data export is selected. Provider data will not train, fine-tune, evaluate or improve models. AI-assisted software development is distinct from those runtime/data uses; this distinction is an intended-use assessment, not a published blanket exemption or legal certification.

On October 31, the normal signed-out browser rendered the [canonical TMDB API terms](https://www.themoviedb.org/api-terms-of-use), [approved branding](https://www.themoviedb.org/about/logos-attribution), [native Movie of the Night terms](https://developers.movieofthenight.com/terms-and-conditions) and [native pricing](https://www.movieofthenight.com/about/api/pricing). No login, agreement acceptance, dashboard, provider contact or provider API request occurred. The web reader remained robots-denied for TMDB terms and unreadable/502 for native pages; normal browser viewing succeeded without bypass. TMDB displays an October 20, 2023 update; no policy date was visible on the native terms/pricing. Retrieval date is not a policy revision date.

| Intended use | Current published evidence | Assessment and remaining boundary |
| --- | --- | --- |
| Private deterministic runtime; no revenue or model use | [TMDB FAQ](https://developer.themoviedb.org/docs/faq) permits attributed noncommercial API use. Canonical terms §§1.A/C and 2.A reserve derivative/AI-application rights and include broad interactive-query/commercial examples. | **Inference:** coding assistance alone does not make this declared runtime an ML product. The FAQ supports the noncommercial basis; it does not override broader terms or establish an explicit development-assistance exception. Preserve source assertions; infer no dataset, chatbot or derivative-product license. |
| Native availability inside the private app | Native §§3/10 permit ordinary application functionality but prohibit competing replication, standalone availability-data distribution and model training/fine-tuning/evaluation/improvement. | **Inference:** the declared source-led companion fits ordinary runtime use rather than those excluded activities. No provider data is supplied to model evaluations; synthetic fixtures remain the development test input. This is not a blanket third-party-content license. |
| Minimal identification and access assertions | Native §5 reserves third-party rights, including service/add-on names and artwork/descriptions; affected content must be removed on notice. | Retain necessary factual IDs, plain identification labels and links with provenance. Omit posters, backdrops, logos of streaming services and descriptions; their omission does not certify every retained field. No affiliation or entitlement follows from a label. |
| Faithful local storage and recovery | TMDB §1.C caps caching at six months; §1.D requires cessation and prompt purge on termination. Native §6 permits functional local retention, including after subscription, subject to the other terms. | TMDB has no perpetual-history permission here. Native retention remains subject to attribution and third-party notice deletion. Backups/restores do not extend any deadline or defeat a purge. |

A provider comparison measures feed behavior, not an ML model. Neither a successful API key nor private deployment independently certifies every intended use. If the runtime becomes AI-based, commercial, a public query/data service or a data product, reassess before enabling that change. No personal preferences, viewing habits or consumer-account login are needed to describe the present use.

## Attribution gap and smallest implementation handoff

At assessed main `c3ed70c`, the report has generic visible offer-source credits, while catalog attribution sits inside collapsed audit details. It contains no approved TMDB logo asset. Caller-supplied credit strings do not guarantee the native provider's required API hyperlink. These are concrete integration gaps, not evidence that a provider is selected.

- **TMDB:** add a compact visible Credits/About block with an [approved, unmodified logo](https://www.themoviedb.org/about/logos-attribution), linked to TMDB, and the prescribed nonendorsement notice. Keep its mark less prominent than the application's. The [FAQ](https://developer.themoviedb.org/docs/faq) specifies placement/branding; canonical §3 supplies the notice. An audit-only text disclaimer does not establish logo compliance, and no plain-text-only exemption was found.
- **TMDB watch providers:** preserve JustWatch credit and the returned TMDB information URL. The [endpoint documentation](https://developer.themoviedb.org/reference/movie-watch-providers) says the response is not a full deep-link feed.
- **Native Movie of the Night:** visible credit must identify Streaming Availability API by Movie of the Night and link to its [API page](https://www.movieofthenight.com/about/api), including written publications. The actual §4 covers application/website display; the pricing FAQ's narrower public-use wording is not used as a private-app exemption.

This document changes no consumer code. The handoff is one shared visible credit block, with source-specific credits when used, rather than repeated disclaimers on every film. Approved provider branding is distinct from unnecessary movie/streaming-service images.

## Conservative candidate request policy — not activated

[Native pricing](https://www.movieofthenight.com/about/api/pricing) still lists Free at **$0 / 1,000 requests per month**, all endpoints/catalogs included, no payment details required. Native §7 and the pricing FAQ specify hard quota suspension without overage charges. An actual account's plan, remaining requests and billing reset are unknown. Marketplace plans are separate; no native allowance is assigned to a RapidAPI key.

[TMDB rate guidance](https://developer.themoviedb.org/docs/rate-limiting) describes a changeable anti-bulk ceiling around 40 requests/second and requires respecting 429. That is not a published monthly allowance, an SLA or a safe target rate; the retired 40-per-ten-seconds limit is not current.

The following are **proposed internal ceilings**, not measured account capacity or a polling schedule:

| Candidate bound | Proposed limit and behavior |
| --- | --- |
| Run scope | At most 60 explicitly selected reviewed title IDs; at most 75 HTTP attempts including retries, pagination and diagnostics. Exhaustion leaves uncompleted work unknown. |
| Pace | Sequential, at most one attempt per second. A published or observed lower provider limit takes precedence. Native burst capacity remains unknown. |
| Native installation budget | At most 750 attempts in any rolling 31 days, including retries, leaving 250 below the published Free allowance. Never reset this counter merely because a process restarts. Other account clients may consume the remaining allowance, so this is no promise of availability. |
| TMDB installation budget | Same bounded run/pace; no monthly entitlement invented. Any later operator cap only reduces use; a response/status can require stopping earlier. |
| Failures | Stop the run on quota exhaustion/429 or authentication/permission failure; do not retry those into a negative offer result. Transport retries remain bounded inside the total attempt cap. Honor a usable Retry-After for a later permitted attempt. |

Any observed lower remaining budget reduces the internal ceiling; an absent header never means unlimited requests. Three nominal 60-title passes require 180 successful requests before retries/other uses, which is arithmetic rather than account-balance evidence. These ceilings are proposals for adoption review, not a mandate to add a new quota-accounting framework now. The parallel candidate adapter work starts with a finite per-run cap. No policy was recorded in the actual database and no live request or scheduled job was started here.

## Retained-copy boundary and remaining decisions

For a candidate TMDB policy, use the earlier of a conservative 180-day deadline and the source's six-calendar-month maximum, subject to earlier termination. Apply it to raw responses, normalized/current/history rows, catalog caches, report/export artifacts and archive/backup/restore copies containing TMDB content. Faithful backup does not renew the clock. Termination requires promptly ceasing use and purging all affected copies, not merely hiding current rows.

For a native candidate, a common internal 180-day ceiling may simplify the same bounded inventory; it is an internal restriction, **not** a provider-required TTL. Third-party removal notices and applicable terms can require earlier deletion. Do not retain images/descriptions merely because §6 permits caching. The existing named-file purge and source-policy primitives do not discover every copy or prove complete enforcement; the selected installation needs an explicit inventory/deletion procedure and an offline copy-purge test before that claim.

The factual uncertainties now separated are actual account balance/tier/reset, unpublished native burst limits, the applicable interpretation of broader TMDB clauses, attribution integration and complete retained-copy enforcement. These are not requests for private user habits. Adoption still requires the actual third B4 date, first-party qualifications and reviewed B8 source/use decision under [ADR 0008](../../adr/0008-availability-providers.md), [ADR 0011](../../adr/0011-cost-rights.md) and [ADR 0012](../../adr/0012-empirical-gates.md). No winner or general compliance certification is declared.
