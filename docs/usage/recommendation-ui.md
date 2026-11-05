# Recommendation website

Browse accepted reviewed films, search titles/directors, filter recognition and
watch history, then open a film to inspect its original evidence. Ratings and
viewing plans are optional. Saved/dismissed controls, Movary actions and a
persistent private deployment are separate slices under [UI epic #98](https://github.com/pavelkrotkov/film-iq/issues/98).

## Start locally

```sh
uv sync --dev
uv run film-iq serve --database path/to/evidence.db \
  --cohort path/to/accepted-cohort.json \
  --snapshot path/to/private/snapshot.json \
  --catalog path/to/reviewed-display.json
```

Repeat `--cohort` for each complete selected accepted revision. Use the same
inputs as the [discovery report](discovery-report.md). Omit `--snapshot` or
`--catalog` when unavailable; neither is a prerequisite. The default listener is
`http://127.0.0.1:8770/`; `--host`/`--port` select the listener. Keep it on loopback
behind the private tailnet HTTPS proxy. This application has no public-user
authentication and is not a public hosting configuration. Stop with Ctrl-C.

Waitress 3.0.2 is the only runtime dependency (ZPL-2.1); Python's reference HTTP
servers discourage production use. The existing repository does not track its
local uv lockfile; the runtime dependency is pinned exactly in the project.
There is no frontend framework, bundler or separate database.

## What the pages mean

The default view excludes films known watched after a successful personal refresh.
Without a snapshot or with a stale/failed refresh, accepted films stay browsable
and their current watched state is unknown. The watch-history filter lets you
include known watched films. Search uses original/reviewed titles and director
names. Recognition filters use exact typed evidence, including preservation,
awards and institutional selections; an unclassified source remains unclassified.

Public-support ordering uses the existing independent-evidence-group baseline.
It is provisional, keeps source order for ties and retains unknown support in its
original slot. It is not a personal prediction. Source ordering remains available.

Film details lead with original evidence links, published ranks/ties or unranked
selection and human evidence types. Expand **Original source record** for exact
edition, original title/year/director, completeness, eligibility and locator.
Typed award facts retain category/recipient meaning; derivative and independent
lineage are not collapsed into extra votes. Reviewed catalog facts remain
separate from original source assertions. Optional personal notes are collapsed.

Viewing options come only from existing rights-permitted retained observations.
Each variant keeps its service, plan/add-on, source/check dates, effective bounds,
price/quality/cut and entitlement uncertainty. An inconclusive attempt remains
distinct from a prior comparable report. No provider call or adoption occurs.
Pages re-read the discovery pipeline on requests so current acceptance and
retention apply; browser responses use `Cache-Control: no-store`.

`/health` checks that configured discovery inputs are readable. It does not assert
fresh personal history, complete source coverage, streaming entitlement or user
satisfaction. Missing/malformed inputs return an unavailable page rather than an
empty catalog. Fix inputs and retry; the UI does not repair or overwrite them.

This slice is read-only. It exposes no raw snapshots, private comments, API
credentials or private rights-review notes. Source text is escaped and external
links are restricted to HTTP(S). It never exposes unresolved film-action routes.
