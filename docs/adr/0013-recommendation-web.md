# ADR 0013 — Small server-rendered recommendation website

**Date:** 2026-11-04  
**Status:** Accepted

## Context

The user authorized a usable FilmIQ recommendation UI after the report/Movary
POC failed to provide browsing, evidence inspection and candidate actions. The
existing modular monolith already supplies accepted/coalesced discovery facts,
reviewed display metadata, typed recognition and rights-filtered offer states.
Rebuilding those contracts or adding a separate frontend stack has no current
benefit. Python's reference HTTP servers discourage production use.

## Decision

Use a small WSGI application, escaped server-rendered HTML, native forms and
responsive CSS. Use [Waitress](https://docs.pylonsproject.org/projects/waitress/en/latest/)
(ZPL-2.1, no runtime dependencies) as the maintained production HTTP server.
This one dependency replaces owning a production HTTP parser/server; no frontend
framework, bundler, ORM, task queue or new authentication service is needed.
Bind loopback behind the existing private tailnet HTTPS infrastructure. Preserve
other services; do not enable public exposure. Keep project data/config/logs in
the attached project folder.

Read through the discovery pipeline on requests, preserving source rights and
expiry at presentation time. Browse accepted reviewed candidates independently
of personal-history freshness; label unknown history rather than presenting an
empty recommendation set as complete. Preserve source rank/ties/unranked status,
original and display assertions, lineage, typed awards/preservation, attribution,
checked dates and unknown access. Never expose private comments or raw snapshots.

Persist only FilmIQ's local saved/dismissed dispositions by reviewed TMDB ID in
the existing SQLite database through a small versioned migration. Default
discovery means neither disposition. Save/dismiss/restore are reversible and
idempotent. Resolve actions against accepted reviewed identities server-side.
Use CSRF protection and safe external links at the actual web trust boundary.
Use the existing approved-watchlist adapter and supported watched-date API;
Movary retains ownership under ADR 0001.

## Consequences / acceptance

Single-user throughput is sufficient; no speculative concurrency infrastructure.
Back up before the live migration; verify existing evidence and reopen/restart
persistence. Supervise with native jobs and a documented private endpoint.
Validate responsive/keyboard browser use, optional-input behavior, provenance,
preview/confirmation and honest API/refresh failure behavior. Extend one meaningful
web integration journey; default pytest collection remains at most 200. Changed
Python functions require CC≤8 and modules MI≥50. Bot and independent exact-head
reviews plus verified CI precede merge. Provider adoption remains a separate gate.

## Reconsideration

Add a frontend framework, richer authentication, a supported Movary rating-write
endpoint or different deployment only for a demonstrated missing task. Do not
turn these possibilities into blockers for the authorized build.
