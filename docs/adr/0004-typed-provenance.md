# ADR 0004 — Source provenance and independent endorsements

**Date:** 2026-10-29  
**Status:** Accepted

## Context
Free-form summaries cannot prove exact author, ranking, festival award, list eligibility or duplicate lineage.

## Decision
Store typed source documents, list editions, ballots/entries, source families, document/extraction revisions, raw titles and citations. Treat aggregators/quoted polls as dependent evidence. Preserve accepted corrections without duplicating votes.

## Consequences
More precise model and review steps; enables reproducibility and re-scoring.

## Validation / reconsideration
Source adapters must prove completeness, rank/tie semantics and source independence on fixtures.

## Ballot and critic identity revision — 2026-10-30

The **independence unit for a named critic's endorsement** is the person/film/evaluation-window relation, not mechanically one publisher, page, aggregate or record. Model publisher/source, edition, source document, individual ballot/author, festival selection/award category, entry, accepted revision and derivation links separately. A publisher poll may aggregate many critics without furnishing their ballots; do not invent known-person counts. The same identifiable critic may publish the same endorsement in Film Comment, BFI or Slant; preserve both records and original ranks, deduplicating only the supported independence unit.

If selecting one published rank per critic/film/window for a rank-aware score, **predeclare the representative source priority**. Do not select the best/highest rank after observing multiple copies; preserve alternative ranks for explanation. Unknown critic identity, source completeness and eligibility remain unknown, not automatically independent or negative.

Manual source inputs (#59) must label **scoped selections** separately from complete publisher editions. Accept only independently checked scope/entry/rank semantics under source-specific rights. Preserve original observations and corrections without duplicate votes.

**Evidence:** [B1 critic-overlap audit](../research/sources/registry.md), [B7 scoring protocol](../research/scoring/study.md), [current best-rank group choice](../../src/film_iq/scoring/__init__.py).
