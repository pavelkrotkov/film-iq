# Recommendation website

Browse accepted reviewed films, search titles/directors, filter recognition and
watch history, then open a film to inspect its original evidence. Ratings and
viewing plans are optional. Save, dismiss and restore controls keep a local
recommendation shortlist. Optional Movary controls preview deliberate personal
actions. The private deployment and its operational evidence are tracked under
[UI epic #98](https://github.com/pavelkrotkov/film-iq/issues/98).

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

## Local shortlist and migration

**Save**, **Dismiss** and **Restore to discovery** are available on film cards
and details. Saved/Dismissed navigation retains the same source evidence and
defaults to all watch-history states, so a later logged watch does not make a
saved film disappear. Discover excludes saved/dismissed films and defaults to
films not known watched. Navigation counts cover current accepted films in each
local state; search and watch/evidence filters can narrow the visible result.
These actions never change Movary's watchlist, history or ratings.

The small disposition table requires schema12. Before upgrading an existing
schema11 installation, stop its writers, create a validated online backup using
[the recovery procedure](../operations-recovery.md#film-iq-recovery), and call the
existing `storage.migrate` helper on the chosen database. The UI does not silently
migrate a live database or create a missing evidence store. Migration preserves
prior evidence; restore a pre-upgrade backup to a new path before rollback.
The new local table is included in ordinary SQLite backups and restore.

Forms require the process's current CSRF token and the configured browser Origin
and Host. Restarting the service invalidates an open old form; reload it before
retrying. The browser-facing URL is explicit when using the private HTTPS proxy:

```sh
FILMIQ_ORIGIN="https://your-tailnet-host:8450"
uv run film-iq serve --database path/to/evidence.db \
  --cohort path/to/accepted-cohort.json \
  --public-origin "$FILMIQ_ORIGIN"
```

Keep the backend on loopback and preserve the original public Host through the
proxy. Forwarded headers do not grant authority. Without `--public-origin`, the
CLI derives the expected local HTTP origin from its host/port. Each action
rechecks accepted reviewed film identity server-side, writes only the local
disposition, then redirects to the updated film page. Repeated actions do not
add duplicate state or change evidence.

## Rate and mark watched

Use **Rate & mark watched** on a film card or detail page. Choose the watch date
and an optional enjoyment score from 1–10, then **Review & save**. The final
**Save rating & mark watched** button commits the displayed film/date/score to
Movary. A blank score keeps the current rating. The date defaults to today in
`TZ` (America/New_York for the current single-user installation) and is editable.
After refresh, the film is excluded from the default unwatched view. It remains
accessible through the watched filter or its saved recommendation state.

Rating entry requires `--rating-command` in addition to the existing read/export
configuration. This trusted operator command accepts a JSON request on stdin:
`username`, positive `tmdb_id`, and integer `rating` (1–10). It must return the
verified `tmdb_id` and `rating` as JSON. No rating value is placed in command-line
arguments or logged. `movary_rating.php` calls Movary 0.82.1's own application
service, using the same method as its native rating editor; no SQL is issued.

For the existing SSH/container installation, construct the JSON argv privately
from the checked-in bridge, with standard shell quoting for the fixed PHP code:

```python
import json
import shlex
from pathlib import Path

code = Path("src/film_iq/movary_rating.php").read_text().removeprefix("<?php")
command = [
    "ssh",
    "-o",
    "BatchMode=yes",
    "your-existing-ssh-alias",
    "docker exec -i movary php -r " + shlex.quote(code),
]
print(json.dumps(command))  # Configure --rating-command; contains no personal values.
```

A verified watch can succeed before a rating/refresh fails. The response retains
that successful result and marks the cache stale; retrying the same date does
not add another play. No live personal ratings are required for acceptance.
Without the bridge, watched logging and the native rating-editor link still work.

## Optional Movary controls

Open **Movary history and watchlist · optional** on a film. **Preview watchlist
addition** shows the exact film before **Confirm this Movary change** adds it to
Movary's intentional watchlist. **Cancel** makes no Movary request. A FilmIQ
**Save** remains a separate local recommendation choice.

**Preview watch date** requires an explicit date and the same confirmation.
Logging an already recorded positive-play date is a no-op; a new date is added
without replacing other dates, plays, ratings or comments. Movary may remove the
film from its watchlist according to its settings, as disclosed in the preview.
No repeated-viewing count editor or automatic suggestion promotion is provided.

**Edit enjoyment rating in Movary** opens the native film page only when the
private snapshot supplies its validated Movary ID. The installed bearer API has
no rating-write endpoint; enjoyment and artistic merit remain separate. Return
and use **Refresh history and ratings**, which performs only complete read APIs
and CSV exports. A failed refresh preserves prior values and marks them stale.
A verified personal write followed by failed refresh is reported as saved with
stale FilmIQ state; uncertainty is not reported as an automatic rollback.

To enable controls, supply `--snapshot`, both `--ratings-command` and
`--history-command` JSON argument arrays, and `MOVARY_URL`, `MOVARY_USERNAME`,
`MOVARY_TOKEN` through the private server environment. Each exporter must emit
its complete CSV to stdout; reuse the installation's existing read-only exporter
arrays from [the personal-refresh workflow](personal-refresh.md). Never put
credentials in these arguments. Missing configuration leaves browsing available.

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

The website exposes no raw snapshots, private comments, API
credentials or private rights-review notes. Source text is escaped and external
links are restricted to HTTP(S). It never exposes unresolved film-action routes.

## Private native deployment

Keep code, SQLite, private inputs, process configuration, and logs inside the
attached project. The selected deployment uses Waitress bound to Mac loopback,
a native supervised SSH reverse tunnel, and the tailnet server's existing
Tailscale Serve HTTPS proxy. No project data is copied to the tailnet server.
No public listener or Funnel is needed. The service requires the Mac to be awake and its user session active.

Project-local configuration lives in `.cache/ui-build/runtime/`:

- `com.filmiq.ui.plist`: `uv run --offline --env-file` starts `film-iq serve`
  with absolute installation paths, loopback binding, and project-local caches.
  Its `--public-origin` must match the configured browser HTTPS origin and port.
  The selected installation also supplies both complete exporter arrays for
  optional Movary controls; credentials are loaded privately from its environment.
- `com.filmiq.ui.tunnel.plist`: SSH forwards the tailnet server’s loopback port8770
  to the Mac's `127.0.0.1:8770`, using existing SSH authentication. Batch mode and
  failure-on-forwarding-error prevent a stalled password prompt or false start.
- UI/tunnel stdout and stderr logs are private files in the same directory.

Both jobs use native `KeepAlive` and bounded restart throttling. Store plists
with mode 0600 and logs/configuration under a mode-0700 private directory.
Do not print credentials or raw personal snapshots when inspecting failures.

Register the project-local plists directly, after checking both loopback ports
are free and the merged application is installed. Run from the attached project
root and set the existing SSH alias and the private URL selected for this installation:

```sh
FILMIQ_PROJECT="$(pwd -P)"
FILMIQ_SSH_HOST="your-existing-ssh-alias"
FILMIQ_ORIGIN="https://your-tailnet-host:8450"
launchctl bootstrap gui/$(id -u) "$FILMIQ_PROJECT/.cache/ui-build/runtime/com.filmiq.ui.plist"
launchctl bootstrap gui/$(id -u) "$FILMIQ_PROJECT/.cache/ui-build/runtime/com.filmiq.ui.tunnel.plist"
ssh "$FILMIQ_SSH_HOST" 'tailscale serve --bg --yes --https=8450 http://127.0.0.1:8770'
```

Open the configured `$FILMIQ_ORIGIN/` after verifying it. Preserve every
existing Serve route; never use `tailscale serve reset`. An added Serve route
alone does not prove the UI is running. Verify the HTTPS response, native process
state, loopback listener, and existing Movary service before reporting success.
Registration by absolute project path persists process restarts within the user
session; after logout/login, bootstrap these project-local jobs again. No
login-startup installation or reboot persistence is implied by this procedure.

## Refresh, restart, and update

The existing `com.filmiq.discovery.daily` job refreshes the personal snapshot
through supported read APIs and complete native CSV exports, then writes the
report and a SQLite online backup. It performs no Movary writes or production
provider polling. Preserve its existing selected cohorts and exporter commands.
The separate B4 observation jobs are not UI jobs and must not be repurposed.

Inspect or restart only the selected UI jobs:

```sh
launchctl print gui/$(id -u)/com.filmiq.ui
launchctl print gui/$(id -u)/com.filmiq.ui.tunnel
launchctl kickstart -k gui/$(id -u)/com.filmiq.ui
launchctl kickstart -k gui/$(id -u)/com.filmiq.ui.tunnel
```

For an application update, stop the UI before changing its installed revision.
Use only reviewed merged code, run `uv sync --dev`, preserve a pre-migration
online backup, then bootstrap the UI again and verify browse/detail and saved
state. The tunnel may remain registered while the application is stopped.
Stop the jobs without deleting their configuration or data:

```sh
launchctl bootout gui/$(id -u)/com.filmiq.ui
launchctl bootout gui/$(id -u)/com.filmiq.ui.tunnel
```

If deliberately withdrawing the endpoint, remove only the dedicated route with
`ssh "$FILMIQ_SSH_HOST" 'tailscale serve --https=8450 off'`. Do not alter Movary's existing route
or unrelated private services.

## Backup and recovery

Back up SQLite through its online backup API before a schema migration; never
copy only the live main file while WAL is active. Save the selected Git revision,
lockfile, private service configuration, cohort/catalog inputs, personal
snapshot/status, and local dispositions under their existing privacy and source
retention rules. Restoring metadata does not extend its original retention lease.

Use the [existing recovery procedure](../operations-recovery.md), restoring into
a new project-local database first. Verify integrity, foreign keys, schema,
accepted evidence, and saved/dismissed state before switching a stopped service
to the restored path. A backup restores only its captured state; preserve the
original database for diagnosis. Do not edit Movary's database or manufacture
personal actions to test recovery.

## Deployment acceptance

The deployment issue [#102](https://github.com/pavelkrotkov/film-iq/issues/102)
records dated operational evidence. Preparation, process registration, HTTP
checks, browser checks, and user satisfaction are separate claims. Record actual
checks and remaining limitations before accepting the integrated UI. In
particular, verify the refreshed Plex history, keyboard/mobile layout, original
source links, filters, local save/dismiss/restore, honest stale/error states,
and restart persistence without live personal-state writes.
