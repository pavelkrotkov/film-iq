# ADR 0013 — Two independent personal film scores

**Date:** 2026-10-30  
**Status:** Accepted user requirement; interim Movary read/export route provisional

## Context

The viewer wishes to express two different subjective evaluations of a watched film. Movary 0.82.1 has one native film-level 1–10 personal rating, and supports a free-text comment on an individual viewing. The documented Ratings CSV contains `userRating`; the separate History CSV contains `watchedAt` and `comment`. The first live film-iq test exported **zero real ratings** and did not exercise a nonempty tagged comment; its ability to capture the second score automatically is **unverified**. Film-IQ also estimates source-backed external critical recognition; that is a different thing from the viewer's artistic judgment.

## Decision

Represent distinct nullable **1–10** user-supplied fields:

- **`personal_enjoyment`** — how entertaining, engaging, watchable or rewarding the film was *to the user*. Enter through Movary's existing film-level personal rating (`userRating`).
- **`personal_artistic_merit`** — the user's own assessment of filmmaking quality, artistic achievement, originality/depth/significance, *irrespective of enjoyment*. Enter initially as an explicit **`Artistic merit: N/10`** token in a Movary per-play comment, with the remaining comment preserved as user-authored prose.

Retain **`external_critical_recognition`** from independently sourced original critic, poll, festival/award evidence as a separate public dimension; a future **`predicted_personal_enjoyment`** may be modeled only after enough actual rated films and independent validation. No external review score automatically becomes a personal artistic-merit score, nor is one subjective score a proxy for the other.

Film-IQ's first-use ingestion creates a private, timestamped **derived snapshot** with source, film/TMDB crosswalk, viewing-date provenance, nullable missingness and explicit conflicts. Treat the tag as a film-level user statement recovered from a *per-play* field: multiple consistent tagged viewings can agree, but differing valid tags require visible resolution and must not silently choose the highest/latest. Ignore nonmatching free-text numbers. The existing private Movary data must not be rewritten or deleted by the read-only sync.

**Contingency:** First verify that the installed Movary version exposes a complete nonempty History CSV or documented read endpoint for comments, alongside full replacement ratings export. If not, allow only an explicit **user-owned local private merit CSV** as a temporary, labeled alternative input; do not assume a hidden API or access Movary's database directly. Propose a narrow upstream configurable multi-rating enhancement via C9 #27 only after measuring a genuine UX/data limitation, and seek approval before coding or forking.

## Consequences

The user can record watch history and enjoyment **immediately** in Movary, and may add artistic-merit tags now; extracting them reliably is an MVP test, **not yet delivered**. The first Film-IQ shortlist can show both scores where present, treat missing values as unknown, exclude watched titles, and display public-source recognition separately. Neither score is automatically trained upon; C6 remains conditional.

## Validation / reconsideration

C0a #58 must, with authorized authentic user entries:
1. Read back at least one nonempty rating and one actual tagged viewing comment through a supported route, matched to the correct movie/work ID.
2. Confirm a changed rating, removed rating, edited/removed merit token and repeated/conflicting viewing comments are handled without lost data or silent selection.
3. Exercise rated-only/unwatched records and complete failed-refresh rollback with credential-free fixture tests.
4. Demonstrate C7 #25 rendering of both personal dimensions and source-backed recognition without public leakage.

If comments fail as a lossless film-level second-score transport, evaluate the smallest documented manual import/upstream enhancement before adding a new ratings UI. Do not promise a native second Movary score until it exists.

## Evidence

- [Gate A real API/empty ratings export](../a7-live-validation.md)
- [Movary movie tracking](https://docs.movary.org/user-guide/tracking-movies/)
- [Movary history versus ratings CSV](https://docs.movary.org/user-guide/personal-data/)
- [MVP issue #58](https://github.com/pavelkrotkov/film-iq/issues/58), [conditional upstream issue #27](https://github.com/pavelkrotkov/film-iq/issues/27)
