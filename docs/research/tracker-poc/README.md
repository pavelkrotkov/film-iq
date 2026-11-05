# Kaneo and YouTrack comparison — work in progress

This is an isolated evaluation, not a change to FilmIQ's accepted architecture.
Movary remains the source of truth for real watched history, ratings, and the
intentional watchlist. The user authorized a separate local import of existing
candidate records and a read-only watched-history view. Use fictional records
and users for destructive, workflow, authorization, and performance tests.
The [working comparison](comparison.md) maps the evidence and gaps to the
requested evaluation criteria; scores remain pending.

## Evidence collected so far

* The local YouTrack `2026.2.19728` instance completed initial setup and its
  API returned HTTP 200. Its Docker base URL was corrected to
  `http://localhost:18180` using JetBrains' documented `configure` command.
  Administrator sign-in worked, and the YouTrack UI created the synthetic
  `FILMPOC` project and issue `FILMPOC-1`, with a fictional title and synopsis.
  See [changing the base URL](https://www.jetbrains.com/help/youtrack/server/change-base-url-listen-port.html).
* A preliminary full-page React widget package can be built with
  `python3 docs/research/tracker-poc/build_youtrack.py` after installing the UI
  dependencies. It uses `host.fetchYouTrack` for issue reads and synopsis edits,
  and builds a ZIP under `.cache/tracker-poc/`. The first version installed and
  rendered in a main-menu iframe, but its issue search returned HTTP 400 because
  `id` is not a valid sort field. After correction to `{issue id}`, the widget
  loaded a fictional issue, saved an edited synopsis and read it after a page
  reload. The newer package adds a richer UI and per-user handlers, but has not
  yet been installed or verified; it is not a complete YouTrack POC.
* Kaneo source inspected: release `v2.49.0`, commit
  `e0ebc61748654f4e33e713dcb441be726ec1cfc4`. Its custom-field schema
  supports text, number, date, dropdown, boolean, and multiselect. Values are
  stored as strings; multiselect values are JSON arrays. A value is keyed by
  task and field, not by task, field, and user. Numeric and multiselect fields
  were also verified against the running API. See [schema](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/src/custom-field/schema.ts),
  [validation](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/src/custom-field/controllers/set-custom-field-value.ts),
  and [migration](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/drizzle/0045_fantastic_princess_powerful.sql).
* Kaneo's source configures credentialed CORS with explicitly configured
  origins in production, and publishes an OpenAPI endpoint. These observations
  do not establish that a separate frontend works or that every endpoint is a
  stable public contract. Verify against the running instance.
* Kaneo's board endpoint is paginated: its documented source defaults to 50
  tasks and caps a page at 100, with separate pages for related information.
  The source lists built-in task sort keys but no custom-field sort key. The
  project custom-field endpoint returns values across the project. Whether
  another supported API provides the required numeric query remains untested;
  any client-side join would need measurements at 1,000 films.
  [Task endpoint](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/src/task/index.ts),
  [query schema](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/src/task/schema.ts),
  [field endpoints](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/src/custom-field/index.ts).
* YouTrack documents `MAIN_MENU_ITEM`, `PROJECT_TAB` and issue-page widget
  extension points. `showHeader: false` hides the page header for a main-menu
  widget, but does not prove the rest of the surrounding interface can be
  hidden. [Extension points](https://www.jetbrains.com/help/youtrack/devportal/apps-reference-extension-points.html).
* YouTrack extension properties can attach app-owned data to user entities, but
  deleting the app deletes its extension-property values. Extension-property
  search does not replace native range filtering or sorting in issue lists.
  A per-user film map is therefore a candidate to test, not a demonstrated
  storage or authorization solution. [Properties](https://www.jetbrains.com/help/youtrack/devportal/apps-extension-properties.html),
  [FAQ](https://www.jetbrains.com/help/youtrack/devportal/apps-faq.html).
* The [current YouTrack pricing page](https://www.jetbrains.com/youtrack/buy/)
  describes free plans for up to ten users for Cloud and Server. Cloud includes
  30 GB; check current terms and other limitations before deployment.
* [YouTrack Cloud](https://www.jetbrains.com/help/youtrack/cloud/about-youtrack-cloud.html)
  is hosted, updated and backed up by JetBrains. [Custom app ZIP uploads](https://www.jetbrains.com/help/youtrack/cloud/manage-apps.html)
  are documented for Cloud, subject to permissions and size limits. Updates are
  rolled out by JetBrains, so record the actual tested Cloud build rather than
  assuming it stays pinned; see the [maintenance calendar](https://www.jetbrains.com/help/youtrack/cloud/youtrack-cloud-maintenance-calendar.html).
  [Database exports](https://www.jetbrains.com/help/youtrack/cloud/database.html)
  are available, but Cloud restores are managed by JetBrains support. These are
  documented capabilities, not live Cloud test results.
* YouTrack documents `host.fetchYouTrack()` as using the current user's session,
  with REST permissions applied at the target endpoint. Widget visibility alone
  is not proof of authorization. Most collection endpoints default to at most
  42 results; the issues resource documents its own export limit, so explicit
  paging is required. [Authentication](https://www.jetbrains.com/help/youtrack/devportal/apps-faq.html),
  [pagination](https://www.jetbrains.com/help/youtrack/devportal/api-concept-pagination.html),
  [issues API](https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues.html).
* YouTrack's documented scheduled rules run as a special workflow user with a
  full set of permissions, which cannot be narrowed. This is an operational
  consideration for a scheduled enrichment workflow; the rule and its scope
  have not yet been tested on the local instance.
  [On-schedule rules](https://www.jetbrains.com/help/youtrack/devportal/on-schedule-rules.html).
* FilmIQ already has a TMDB/JustWatch availability normalizer that distinguishes
  subscriptions, rentals, purchases, free and ad-supported offers. Its missing
  and malformed responses do not imply removal. Reuse it when implementing the
  worker; it does not fetch or retain the data by itself.

## Synthetic dataset

`python docs/research/tracker-poc/fixture_data.py 30` writes a deterministic
30-film JSON dataset to stdout; pass `1000` for the larger dataset. Redirect
output to an ignored file within the project folder if needed. It contains two
synthetic users with independent preferences. Fixture IDs are deliberately not
TMDB IDs, and must never be submitted to TMDB or presented as verified films.
The Kaneo film seeder loads canonical fixture attributes. A separate preference
seeder loaded 30 films for each synthetic user, with a second run adding zero.

## Kaneo experiment

The user-authorized private input was rebuilt from a fresh read-only Movary
snapshot and accepted discovery evidence: 103 reviewed unwatched candidates and
27 watched records with supplied TMDB IDs. Watched-only IDs are Movary-supplied
and were not independently reverified here. Source-listed years are not treated
as verified release years. The input and real-data outputs remain in the ignored
private cache; see [private input preparation](private-inputs.md).

An isolated Kaneo workspace contains 130 canonical records, with zero created on
a repeat import. An unrelated signed-in viewer could not access the project.
A separate, project- and user-gated Movary sidecar contains 27 watched records,
including repeat observations and unknown dates; it does not alter Movary or
Kaneo's canonical fields or editable preferences. Two-user and denial checks
passed for the sidecar, but its actual rendering in the browser has not been
verified. The real-data import contains source-list assertions and links, not
TMDB API response bodies. Source terms and upstream provenance still govern
retention; this experiment does not establish unrestricted reuse.

The optional local TMDB reader fetches metadata and offers on demand without
writing responses into tracker history. Page-memory batches are limited to 30
films at a time and are explicitly initiated. Required credits and unknown
states are included in the UI, but visual rendering and provider accuracy have
not been validated. One prior example-ID read succeeded; no user entitlement
was established. The restarted reader requires a Kaneo session and the local UI
origin: an anonymous request returned 401 and a signed-in synthetic user
received 200 for TMDB's example ID. It is a local POC, not a multi-host
credential gateway.

An aggregate, non-retaining coverage check on 2026-11-05 requested details for
all 130 supplied IDs: 130 responses returned the requested ID and a title, and
all 130 included a synopsis, poster path, genre, director and parseable release
date. After Unicode, case and whitespace normalization, 110 returned titles
exactly matched the input title; 20 did not. Different titles can be legitimate
alternates and this check does not establish identity. It queried no provider
availability and retained no TMDB response bodies. Coverage is not evidence of
provider accuracy, film identity, rights clearance or persistent enrichment.
The check can be repeated using `tmdb_coverage.py --input
.cache/tracker-poc/private/film-input.json --live` with an existing TMDB
credential in the environment. Omit `--live` for a no-request preview. It
paces requests and stops on authentication, permission or rate-limit errors;
it prints aggregate counts only. The original check was a one-time read, not a
scheduled sync.

The pinned Kaneo `2.49.0` image and PostgreSQL `16.15` ran locally on
2026-11-05. The running `/api/openapi` document was inspected. In a private
synthetic project, `kaneo_smoke.py` created a task with a synthetic identifier,
updated its description and column, wrote a numeric custom field and a JSON
multiselect, and read the results back. A nonnumeric update returned HTTP 400;
an unauthenticated description update was rejected, and the prior description
remained intact. A second run reused the same fixture. A separate synthetic
viewer could read the film but received HTTP 403 when editing it; the existing
description remained unchanged. The same test archived and restored the record
without losing its synopsis or custom fields, and created/read a synthetic
comment. Concurrent imports have not been tested.

The 30-record seed added 29 tasks after the smoke test created the first. The
1,000-record seed added 970 tasks in 17.71 seconds, and a repeat added zero.
On this Docker Desktop installation, a single complete board traversal returned
1,000 unique tasks in ten requests in 0.234 seconds; a subsequent project-wide
read returned 3,999 custom-field values in 0.044 seconds. These are single local
API measurements, not browser, concurrency, production, or upgrade benchmarks.
The first record came from the smoke test and has a different set of fields.
Two additional local search calls took 21.8 ms for `Fictional Film` and 14.2 ms
for `Fictional Film 0100`. The broad search returned 50 results and reported
`totalCount: 50` even though all 1,000 synthetic titles contain that phrase.
In this version the search schema caps `limit` at 50 and provides no paging
parameter; do not use its reported count to assert a complete extraction.
The paginated board traversal above is a different endpoint.

An initial React UI builds and is served locally. It reads board pages and custom
fields using the current Kaneo browser session; it can submit a synopsis or
column change through the API. The server accepted authenticated requests with
the UI origin and returned the correct CORS headers. **The actual browser has
not been tested** because a separate browser surface was unavailable and the
user's Brave session was in use. The private project includes source-identified
real records, and metadata read-through is optional and nonpersistent. Synthetic
add, archive, comment and preference controls are wired to the APIs but have not
yet been verified in a browser. Its rendering at 1,000 films has not been
measured. Do not represent it as the completed Kaneo POC.

Fixture representation: task title and description hold title and synopsis;
`POC Fixture ID`, `POC Year`, `POC Genre`, and `POC Subscription Providers`
are task-wide custom fields. `to-do`, `in-progress`, `in-review`, and `done`
are used as approximate fixture columns; `done` is not Kaneo's archive feature.
The UI labels missing provider data as unknown. The generated preferences,
rentals and checked timestamps have not been persisted for the full seeded dataset.
The first 30 films also have synthetic critic scores and summaries; reseeding
fills only missing critic fields and preserved the existing smoke-test score.

### Per-user preference bridge

Kaneo custom fields are task-wide, so the POC uses one small SQLite file at
`.cache/tracker-poc/preferences.sqlite3` for `(Kaneo user ID, task ID)` scores,
watchlist flags, watched timestamps and notes. Test it with synthetic data;
Movary remains authoritative for real personal state. A missing watchlist value
remains unknown rather than being inferred from an interest score. The loopback-only bridge
resolves the current user through Kaneo's session and checks the user's task
read access before writes. Preference reads return only that user's rows; a user
who later loses access to a task can still retrieve their own stored preference
row, but the UI receives film metadata only from Kaneo. A deployment would need
to assess this revocation behavior, storage retention and backup separately.

Changes require a server-generated preview and a separate confirmation request;
the preview binds the user, record, previous values and proposed values. The
React UI requests this preview and presents a confirmation before saving. The
preview key is process-local and previews expire when the bridge restarts. The
application joins and numerically sorts the current user's preferences in the
browser; these scores are not queryable or sortable by Kaneo's native search.
The API check verified two users with distinct values, rejection of another
user's preview token and unauthenticated access, and persistence after restart.
A live check joined all 1,001 Kaneo tasks to both users' preferences and ran the
same UI filter code: Netflix with interest at least eight returned fixture IDs
0008 and 0028 for user A, and 0004, 0016 and 0024 for user B. Numeric ordering
placed scores of ten first. A separate deterministic fixture check covers
numeric sort and availability freshness. The React controls, visual layout and
1,000-film rendering remain unverified in a browser.

The updated YouTrack app's personal preference preview stores only the fields
needed to bind the confirmation, not draft notes. Its cancel action discards
the pending preview. The code and fictional checks have not yet been installed
or validated in the YouTrack runtime. YouTrack's per-project Movary snapshot
handler likewise has synthetic checks only; concurrent imports are unverified.

The separate `enrichment.py` worker uses a backend protocol and the existing
FilmIQ availability normalizer. Its only source is explicitly fictional, with
IDs that are not TMDB IDs. `kaneo_enrich_check.py` imports a fictional record,
repeats the import, and verifies that a user-edited synopsis, genre and note
survive. It stores complete synthetic subscription/rental/purchase observations
and their checked timestamp together in a single text field. A missing,
malformed or failed provider response preserves the previous observation. This
is a sequential fixture test. A corresponding YouTrack adapter also passes a
synthetic repeat, lifecycle and failure-preservation check. Neither adapter
persists live TMDB responses, and concurrent imports are not tested. Task-wide
notes are not per-user preferences.

On 2026-11-05, two read-only requests using the existing project credential
checked TMDB's documented example movie ID 11: both the movie-details and
watch-providers endpoints returned the requested ID. The existing normalizer
classified the US provider response as complete with 12 reported offers. No
response body or API key was saved in the POC or committed, and no personal
entitlement or provider accuracy was verified. The read-only `tmdb_readonly.py`
adapter subsequently fetched the same ID's metadata, genres, director, poster
URL and US offers; its separate deterministic check exercises unavailable
provider handling. It does not implement or validate a live TMDB-to-tracker
import. [Movie details](https://developer.themoviedb.org/reference/movie-details),
[watch providers and JustWatch attribution](https://developer.themoviedb.org/reference/movie-watch-providers).

## Reproduce the isolated Kaneo experiment

Use this worktree's root as the current directory. Docker Desktop stores images
and runtime data in its VM outside the worktree; the project-specific persistent
directories and generated secrets are under the ignored `.cache/tracker-poc/`.
The following creates missing directories and a local-only random secret file
without replacing existing secrets:

```sh
python3 - <<'PY'
from pathlib import Path
import secrets
root = Path('.cache/tracker-poc')
for name in ('postgres', 'youtrack/data', 'youtrack/conf', 'youtrack/logs', 'youtrack/backups'):
    (root / name).mkdir(parents=True, exist_ok=True)
path = root / 'secrets.env'
if not path.exists():
    path.write_text('\n'.join([
        'KANEO_CLIENT_URL=http://localhost:15173',
        'CORS_ORIGINS=http://localhost:15173,http://localhost:15174',
        'POSTGRES_DB=kaneo', 'POSTGRES_USER=kaneo',
        'POSTGRES_PASSWORD=' + secrets.token_hex(24),
        'AUTH_SECRET=' + secrets.token_hex(32), '',
    ]))
    path.chmod(0o600)
PY
docker compose -f docs/research/tracker-poc/compose.yaml up -d postgres kaneo
python3 docs/research/tracker-poc/kaneo_bootstrap.py --directory .cache/tracker-poc
```

The bootstrap prints the project ID and stores the synthetic user credential
and cookie jar in that ignored directory. Supply the printed project ID to the
following commands; use the same ID to open the UI. The seed is repeatable
sequentially but is **not safe for simultaneous seeders**.

```sh
POC_PROJECT_ID='<printed project ID>'
python3 docs/research/tracker-poc/kaneo_smoke.py --project "$POC_PROJECT_ID" --cookie-file .cache/tracker-poc/kaneo-cookies.txt
python3 docs/research/tracker-poc/kaneo_viewer_check.py --directory .cache/tracker-poc
uv run python docs/research/tracker-poc/kaneo_enrich_check.py --directory .cache/tracker-poc
uv run python docs/research/tracker-poc/tmdb_readonly_check.py
python3 docs/research/tracker-poc/kaneo_seed.py --project "$POC_PROJECT_ID" --cookie-file .cache/tracker-poc/kaneo-cookies.txt --count 1000
python3 docs/research/tracker-poc/kaneo_benchmark.py --project "$POC_PROJECT_ID" --cookie-file .cache/tracker-poc/kaneo-cookies.txt
```

In a second terminal, start the preference bridge from the worktree root:

```sh
uv run python docs/research/tracker-poc/preferences.py
```

Then, from the worktree root in the first terminal, run the two-user check and
start the UI:

```sh
uv run python docs/research/tracker-poc/preferences_check.py --directory .cache/tracker-poc
uv run python docs/research/tracker-poc/preferences_seed.py --directory .cache/tracker-poc --count 30
uv run python docs/research/tracker-poc/live_filter_check.py --directory .cache/tracker-poc
python3 docs/research/tracker-poc/fixture_data.py 30 | node docs/research/tracker-poc/ui/filter_check.mjs
cd docs/research/tracker-poc/ui
npm ci --cache ../../../../.cache/npm --no-audit --no-fund
npm run build
python3 -m http.server 15174 --bind 127.0.0.1
```

Sign in to `http://localhost:15173/auth/sign-in` using the synthetic account in
`.cache/tracker-poc/kaneo-test-user.json`, then open
`http://localhost:15174/?project=<printed project ID>`. The API and UI are
bound to loopback; this configuration is for isolated local evaluation only.
React and esbuild are MIT-licensed. The UI includes no service API key.

## YouTrack status

The user selected local YouTrack Server for this evaluation and identified
Hermes as a possible eventual host. No Hermes installation, deployment, data
transfer, resource measurement or operating-cost test has been performed; the
current POC runs on the Mac. Cloud remains a documented alternative above.

The pinned `2026.2.19728` server runs at `http://localhost:18180/`. Database,
configuration, logs and backup directories are bind-mounted under
`.cache/tracker-poc/`. The user completed setup and granted a local integration
token, stored only in the ignored project cache. The `FILMPOC` project is for
fictional tests; `FILMREAL` holds the 130 authorized canonical film records.
Repeated canonical imports created no duplicates and never copied personal
ratings, notes, watchlist state, or TMDB API response bodies into issues.
The 130 records now have a sanitized source-provenance field, backfilled only
where missing; exact input provenance remains in the ignored private manifest.
A repeat backfill changed zero records. Source evidence IDs and links are
validated before any import writes, and source-listed years remain assertions.
Anonymous issue access returned HTTP 401; signed-in low-privilege access to
the real project has not been tested. Two fictional local accounts were added
only to the synthetic project team. An administrator's effective-role query
reported a Read Issue assignment for each account in FILMPOC and none in
FILMREAL; the same query returned three assignments for the administrator in
FILMREAL as a positive control. This is role-assignment evidence, not an
impersonated issue request or proof of issue-level visibility. See the
[documented scope and holder query semantics](https://www.jetbrains.com/help/youtrack/devportal/api-access-management-query-syntax.html).

The common synthetic dataset created 30 issues, then 970 more in 26.990 seconds.
A single local read traversed and numerically sorted 1,000 issues by a typed
global critic-score field in 0.348 seconds. These do not establish native
per-user interest queries, browser rendering, concurrent performance, or
production capacity. The synthetic API exercise verified state values,
comments and history, rejection of a nonnumeric integer and an invalid state,
preservation of a user-edited synopsis and provider observation, repeat import,
and anonymous read/write denial. The separate programmed workflow and per-user
extension properties have only passed mock checks and await a live test.

The earlier embedded widget passed an actual synopsis edit/reload. The pending
update adds preferences, watched-history support and synthetic workflows; the
app's permission and data-loss behavior must be tested before real watched data
is imported into its per-user property. MDBList read-through is implemented
without retention, but the live API returned HTTP 403 for an unknown reason.
No product score or recommendation is justified yet.

## Outstanding

The complete comparison, equivalent applications, browser-level multiuser
preference isolation, usable live enrichment across both frontends, browser demonstrations,
signed-in YouTrack permission tests, upgrade assessment, weighted scores,
and recommendation remain outstanding. Do not score or recommend either
product from the current evidence. Docker Desktop's external runtime storage
under `/var/lib/docker` was approved by the user on 2026-11-05.
