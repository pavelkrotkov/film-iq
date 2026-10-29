# Gate B — working evidence matrix

**Status:** In progress, not a gate decision. Updated 2026-10-29.

**Scope:** [Epic B](https://github.com/pavelkrotkov/film-iq/issues/2) and [issue #18](https://github.com/pavelkrotkov/film-iq/issues/18); [plan](../../plan.md#epic-b--explore-source-universe-and-provider-quality); ADRs [0005](../adr/0005-extraction-choice.md), [0006](../adr/0006-scoring-separation.md), [0008](../adr/0008-availability-providers.md) and [0012](../adr/0012-empirical-gates.md).

The table is a working index, not evidence that any issue is complete. Link each report and record its actual sample, errors, labor, costs, rights and unresolved questions as its evidence is reviewed. Gate B requires the relevant B1–B7 evidence or explicit inconclusive outcomes; do not change provisional decisions on preliminary leads alone.

| Issue | Decision or evidence needed | Current status |
|---|---|---|
| [B1](https://github.com/pavelkrotkov/film-iq/issues/11) | Source priorities, eligibility, independence and rights | [Registry draft](https://github.com/pavelkrotkov/film-iq/pull/36): 11 source families; source permissions and some eligibility remain unresolved. |
| [B2](https://github.com/pavelkrotkov/film-iq/issues/12) | Historical and specialty-title identity coverage | [Sample draft](https://github.com/pavelkrotkov/film-iq/pull/39): 14 exploratory cases with cached or inaccessible lookups; no current coverage or automated precision estimate. |
| [B3](https://github.com/pavelkrotkov/film-iq/issues/13) | Audited extraction cohort, held-out methods and recovery | [Benchmark draft](https://github.com/pavelkrotkov/film-iq/pull/40): synthetic checks include a 47/50 failure and two-record SQLite/dlt rollback/retry comparison; candidate pages are not a gold corpus. |
| [B4](https://github.com/pavelkrotkov/film-iq/issues/14) | Provider coverage, offer correctness, rights, cost and change timeliness | [Cohort draft](https://github.com/pavelkrotkov/film-iq/pull/41): 60 candidates, not yet identity-audited; no three-date comparison or account entitlement validation. |
| [B5](https://github.com/pavelkrotkov/film-iq/issues/15) | Authorized long-tail leads and library eligibility | [Access draft](https://github.com/pavelkrotkov/film-iq/pull/37): six leads; US playback and individual entitlement remain unverified. |
| [B6](https://github.com/pavelkrotkov/film-iq/issues/16) | Reuse candidates, licenses and maintenance cost | [Reuse dossier](https://github.com/pavelkrotkov/film-iq/pull/38): pinned module and license inspection; no measured adoption cost. |
| [B7](https://github.com/pavelkrotkov/film-iq/issues/17) | Public-score baselines, independent holdouts and sparse-film behavior | [Scoring draft](https://github.com/pavelkrotkov/film-iq/pull/42): synthetic lineage and scoring comparisons; real holdout remains unrun. |

## Preliminary constraints

- [Film Comment's terms](https://www.filmcomment.com/terms-of-service/) restrict specified automated collection and reuse. Permission to access a page is not a grant to retain or redistribute its contents.
- [TMDB's movie-provider documentation](https://developer.themoviedb.org/reference/movie-watch-providers) requires JustWatch attribution and does not provide full provider deep links. A service listing is not a verified account entitlement.
- [Watchmode's current terms](https://api.watchmode.com/tc) limit free-plan non-image caching to 30 days and require deletion when the account ends. Apply the actual provider and plan terms before retaining observations.
- [Letterboxd's API policy](https://letterboxd.com/api-beta/) currently excludes several categories relevant to this project, including personal and recommendation projects. An open-source scraper license does not supply source-data permissions.

## Decision record

No extraction tool, specialty provider or scoring weights have been selected by this matrix. Record a reasoned decision or an explicit insufficient-evidence outcome only after the relevant reports are available. Changes to cross-cutting ADRs need a separately coordinated review.
