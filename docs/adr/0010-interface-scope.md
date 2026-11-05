# ADR 0010 — FilmIQ recommendation UI; CLI/reports remain supported

**Date:** 2026-10-29  
**Status:** Accepted; amended 2026-11-04 by explicit user direction

## Context
The initial CLI/report decision assumed Movary could be the primary interface.
The populated POC demonstrated a missing task: users cannot browse recommendations,
inspect critic/festival/preservation provenance, or save/dismiss candidates there.
The user explicitly prioritized this interface and authorized planning and delivery
in [UI epic #98](https://github.com/pavelkrotkov/film-iq/issues/98).

## Decision
Make FilmIQ the primary recommendation interface: responsive browse/search/filter,
film details with original evidence links and uncertainty, persistent local
shortlist/dismiss/restore, and deliberate Movary-backed personal actions. Retain
CLI/reports for automation. Missing personal inputs or an unselected production
availability provider must not block browsing or release of this UI.

Reuse the existing Python/SQLite pipeline through native HTML forms and CSS;
see [ADR 0013](0013-recommendation-web.md). Movary remains the personal system of
record under [ADR 0001](0001-movary-ownership.md).

## Consequences
No separate frontend build, duplicate personal store, automatic watchlist
promotion or public multiuser hosting. The installed Movary bearer API supports
watch dates and watchlist actions but no rating write: display ratings and link
to the native film/rating editor until a supported endpoint exists. This concrete
limitation does not gate recommendation UI delivery.

## Validation / reconsideration
The POC missing-task gate is satisfied by the user's observed inability to use
recommendations and explicit build authorization. Acceptance requires a populated,
deployed browser journey, provenance checks and honest failure/freshness behavior;
automated checks do not establish user satisfaction.

