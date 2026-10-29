# B4: US availability benchmark — cohort and protocol

**Version:** 0.1 · **Prepared:** 2026-10-29 · [Issue #14](https://github.com/pavelkrotkov/film-iq/issues/14) · [Epic B](https://github.com/pavelkrotkov/film-iq/issues/2)

**Status:** Cohort candidates and protocol only. No provider observation, account entitlement check, coverage estimate, or three-date comparison has been completed.

This convenience cohort deliberately assigns ten candidates to each of six strata. Assignments are for reporting and may overlap in reality; for example, an older film can also be a short. The samples are not a random or representative estimate of all cinema. Confirm each title against a source, director and an unambiguous provider identifier before freezing the cohort; a year of festival selection or award eligibility is not automatically the production or premiere year. Replace an ambiguous candidate only with a recorded reason and source. Follow [plan §7](../../../plan.md), [ADR 0008](../../adr/0008-availability-providers.md) and [ADR 0011](../../adr/0011-cost-rights.md).

## Candidate cohort

The source references identify the selection frame, not current availability or permission to retain provider data. BFI and Cannes state conditions on links; their URLs below are identifiers pending review of the applicable terms. Lists are titles only; no source text or provider catalog is copied.

| Assigned stratum | Selection frame | Ten candidate films |
| --- | --- | --- |
| Mainstream | Top ten by 2019 domestic gross in [The Numbers' annual chart](https://www.the-numbers.com/market/2019/top-grossing-movies) | Avengers: Endgame; The Lion King (2019); Toy Story 4; Frozen II; Captain Marvel; Star Wars: The Rise of Skywalker; Spider-Man: Far From Home; Aladdin (2019); Joker; It: Chapter Two |
| International arthouse | 2024 Cannes feature selection: `https://www.festival-cannes.com/en/press/press-releases/the-films-of-the-official-selection-2024/` | Grand Tour; All We Imagine as Light; The Seed of the Sacred Fig; Wild Diamond; The Girl with the Needle; The Village Next to Paradise; On Becoming a Guinea Fowl; Black Dog; Viet and Nam; My Sunshine |
| Older | 2022 Sight and Sound retrospective: `https://www.bfi.org.uk/sight-and-sound/greatest-films-all-time` | Tokyo Story; Citizen Kane; Vertigo; 2001: A Space Odyssey; Jeanne Dielman, 23 quai du Commerce, 1080 Bruxelles; Seven Samurai; Meshes of the Afternoon; Pyaasa; Hiroshima mon amour; The River (1951) |
| Documentary features | [2024](https://www.oscars.org/oscars/ceremonies/2024) and [2025](https://www.oscars.org/oscars/ceremonies/2025) Academy Awards documentary feature nominees | 20 Days in Mariupol; Bobi Wine: The People's President; The Eternal Memory; Four Daughters; To Kill a Tiger; No Other Land; Black Box Diaries; Porcelain War; Soundtrack to a Coup d'Etat; Sugarcane |
| Animated features | [2024](https://www.oscars.org/oscars/ceremonies/2024) and [2025](https://www.oscars.org/oscars/ceremonies/2025) Academy Awards animated feature nominees | The Boy and the Heron; Elemental; Nimona; Robot Dreams; Spider-Man: Across the Spider-Verse; Flow; Inside Out 2; Memoir of a Snail; Wallace & Gromit: Vengeance Most Fowl; The Wild Robot |
| Shorts / experimental | 2024 Cannes short competition: `https://www.festival-cannes.com/en/2024/the-short-film-competition-programme/` | Volcelest; Ootidė; Sanki Yoxsan; Les Belles Cicatrices; Rrugës; Across the Waters; Perfectly a Strangeness; Tea; Amarela; The Man Who Could Not Remain Silent |

The source frames overrepresent award nominees, prominent festivals and a single box-office year. They are useful contrasts for an initial experiment, not evidence of provider performance across all films, countries or formats. Regional production, original language, translated titles, premieres and exact IDs still need individual audit. Resolve the overlapping-strata issue before estimating by stratum; never count a film twice within an overall denominator.

## Observation and comparison

1. Freeze the 60 audited identities and record each candidate's assigned stratum, source, director, year fields, TMDB/IMDb identifiers when independently verified, and unresolved status. Do not guess identifiers or silently remove unresolved titles.
2. On **three genuinely separate dates**, query the same candidates in the US through TMDB/JustWatch and Movie of the Night, with targeted MDBList or Watchmode checks only if access and terms permit. Record provider, endpoint, request count, UTC time, status, completeness and freshness. A failed, partial, unsupported or inaccessible request is unknown; a successful complete empty result is a separate observation.
3. Match offers by film, provider, country, access type and add-on, while retaining source-specific observations. Distinguish subscription, free/ad-supported, rent, buy and add-on. A service-level subscription result does not verify a particular ad tier or account.
4. For purchase-driving examples, compare the returned link and access type with the first-party page and, where authorized and feasible, the intended account/plan. Record inaccessible or untested entitlements as unknown. Never infer a removal from a failed or partial request; distinguish first observed by this study from provider-asserted dates.
5. Report valid denominators, unresolved identities, complete versus failed requests, coverage by stratum, known classifications and disagreements, first-party checks, change/expiry timing, request quotas, manual review time and costs. A missing provider response is not a negative result.

| Observation | Date | Provider results | First-party / account verification |
| --- | --- | --- | --- |
| 1 | Pending | Not run; credentials not found among the expected environment variables during initial setup. | Not run |
| 2 | Pending | Not run | Not run |
| 3 | Pending | Not run | Not run |

One preliminary first-party lead was checked through search-indexed page text on 2026-10-29: [Disney+'s *Inside Out 2* page](https://www.disneyplus.com/browse/entity-ec9f9fa3-fbae-4a25-b722-12c3b8ab0ef4?sharesource=Android) identifies the 2024 film and director Kelsey Mann. The indexed page was not a live playback or personal-plan test. It is not a provider-API observation, a confirmed US entitlement, or evidence that the 60-film first observation is complete.

## Rights and operating constraints

- [TMDB's movie-provider API](https://developer.themoviedb.org/reference/movie-watch-providers) uses JustWatch data, requires JustWatch attribution and does not return full provider deep links. Its [FAQ](https://developer.themoviedb.org/docs/faq) describes TMDB attribution and noncommercial API access.
- [Movie of the Night](https://docs.movieofthenight.com/guide/authentication) requires an API key. Its [show documentation](https://docs.movieofthenight.com/guide/shows) describes offer types; a provider's category is not account-level proof.
- [MDBList](https://docs.mdblist.com/docs/api) publishes a free request quota and account-wide short-window limits; permission to retain historical API observations remains unverified.
- [Watchmode's terms](https://api.watchmode.com/tc), updated 2026-10-24, limit free-plan non-image data caching to 30 days and require deletion when an account ends. Check the actual plan and terms before storing or redistributing results.

No provider has been selected as superior. Keep actual provider data, credentials and personal account details out of Git; record only rights-permitted aggregate evidence and an explicit inconclusive result when the comparison cannot be run.
