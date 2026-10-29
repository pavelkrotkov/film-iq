# Gate B — working evidence matrix

**Status:** In progress, not a gate decision. Updated 2026-10-29.  
**Scope:** [Epic B](https://github.com/pavelkrotkov/film-iq/issues/2) and [issue #18](https://github.com/pavelkrotkov/film-iq/issues/18); [plan](../../plan.md#epic-b--explore-source-universe-and-provider-quality); ADRs [0005](../adr/0005-extraction-choice.md), [0006](../adr/0006-scoring-separation.md), [0008](../adr/0008-availability-providers.md) and [0012](../adr/0012-empirical-gates.md).

The table is a working index, not evidence that any issue is complete. Link each report and record its actual sample, errors, labor, costs, rights and unresolved questions as its evidence is reviewed. Gate B requires the relevant B1–B7 evidence or explicit inconclusive outcomes; do not change provisional decisions on preliminary leads alone.

| Issue | Decision or evidence needed | Current status |
|---|---|---|
| [B1](https://github.com/pavelkrotkov/film-iq/issues/11) | Source priorities, eligibility, independence and rights | Original-source audit underway; terms and permissions need source-specific review. |
| [B2](https://github.com/pavelkrotkov/film-iq/issues/12) | Historical and specialty-title identity coverage | Ten exploratory cases include cached catalog pages and inaccessible lookups; no current coverage or automated precision estimate. |
| [B3](https://github.com/pavelkrotkov/film-iq/issues/13) | Audited extraction cohort, held-out methods and recovery | Candidate pages are not a gold corpus; rebalance the source mix and verify rights before testing. |
| [B4](https://github.com/pavelkrotkov/film-iq/issues/14) | Provider coverage, offer correctness, rights, cost and change timeliness | No three-date comparison or first-party entitlement validation has been completed. |
| [B5](https://github.com/pavelkrotkov/film-iq/issues/15) | Authorized long-tail leads and library eligibility | Preliminary catalog and official-upload leads; US playback and individual entitlement remain unverified. |
| [B6](https://github.com/pavelkrotkov/film-iq/issues/16) | Reuse candidates, licenses and maintenance cost | Code and license review underway; no adoption cost benchmark. |
| [B7](https://github.com/pavelkrotkov/film-iq/issues/17) | Public-score baselines, independent holdouts and sparse-film behavior | Original-ballot overlap identified; real holdout comparison remains unrun. |

## Preliminary constraints

- [Film Comment's terms](https://www.filmcomment.com/terms-of-service/) restrict specified automated collection and reuse. Permission to access a page is not a grant to retain or redistribute its contents.
- [TMDB's movie-provider documentation](https://developer.themoviedb.org/reference/movie-watch-providers) requires JustWatch attribution and does not provide full provider deep links. A service listing is not a verified account entitlement.
- [Watchmode's current terms](https://api.watchmode.com/tc) limit free-plan non-image caching to 30 days and require deletion when the account ends. Apply the actual provider and plan terms before retaining observations.
- [Letterboxd's API policy](https://letterboxd.com/api-beta/) currently excludes several categories relevant to this project, including personal and recommendation projects. An open-source scraper license does not supply source-data permissions.

## Decision record

No extraction tool, specialty provider or scoring weights have been selected by this matrix. Record a reasoned decision or an explicit insufficient-evidence outcome only after the relevant reports are available. Changes to cross-cutting ADRs need a separately coordinated review.
