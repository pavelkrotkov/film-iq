# Kaneo and YouTrack comparison — work in progress

This is an isolated evaluation, not a change to FilmIQ's accepted architecture.
Movary remains the source of truth for real watched history, ratings, and the
intentional watchlist. Use synthetic films and users for these experiments.

## Evidence collected so far

* Kaneo source inspected: release `v2.49.0`, commit
  `e0ebc61748654f4e33e713dcb441be726ec1cfc4`. Its custom-field schema
  supports text, number, date, dropdown, boolean, and multiselect. Values are
  stored as strings; multiselect values are JSON arrays. A value is keyed by
  task and field, not by task, field, and user. This is source inspection, not
  a running API test. See [schema](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/src/custom-field/schema.ts),
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
* YouTrack documents `host.fetchYouTrack()` as using the current user's session,
  with REST permissions applied at the target endpoint. Widget visibility alone
  is not proof of authorization. Most collection endpoints default to at most
  42 results; the issues resource documents its own export limit, so explicit
  paging is required. [Authentication](https://www.jetbrains.com/help/youtrack/devportal/apps-faq.html),
  [pagination](https://www.jetbrains.com/help/youtrack/devportal/api-concept-pagination.html),
  [issues API](https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues.html).
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

The pinned Kaneo `2.49.0` image and PostgreSQL `16.15` ran locally on
2026-11-05. The running `/api/openapi` document was inspected. In a private
synthetic project, `kaneo_smoke.py` created a task with a synthetic identifier,
updated its description and column, wrote a numeric custom field and a JSON
multiselect, and read the results back. A nonnumeric update returned HTTP 400;
an unauthenticated description update was rejected, and the prior description
remained intact. A second run reused the same fixture. A separate synthetic
viewer could read the film but received HTTP 403 when editing it; the existing
description remained unchanged. Concurrent imports have not been tested.

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
not been tested**: the initial Mac lock and the later YouTrack setup handoff
prevented it. The UI uses fixture IDs,
not TMDB IDs, and does not implement real posters, reviews, comments, live TMDB
enrichment, or real-film creation. Preference controls are wired to the bridge
described below, but have not yet been verified in a browser.
Its filters and rendering at 1,000 films have not been measured. Do not use it
for personal data or represent it as the completed Kaneo POC.

Fixture representation: task title and description hold title and synopsis;
`POC Fixture ID`, `POC Year`, `POC Genre`, and `POC Subscription Providers`
are task-wide custom fields. `to-do`, `in-progress`, `in-review`, and `done`
are used as approximate fixture columns; `done` is not Kaneo's archive feature.
The UI labels missing provider data as unknown. The generated preferences,
rentals and checked timestamps have not been persisted for the full seeded dataset.

### Synthetic per-user preference bridge

Kaneo custom fields are task-wide, so the POC uses one small SQLite file at
`.cache/tracker-poc/preferences.sqlite3` for `(Kaneo user ID, task ID)` scores,
watchlist flags, watched timestamps and notes. It is for synthetic data only;
Movary remains authoritative for real personal state. The loopback-only bridge
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

The separate `enrichment.py` worker uses a backend protocol and the existing
FilmIQ availability normalizer. Its only source is explicitly fictional, with
IDs that are not TMDB IDs. `kaneo_enrich_check.py` imports a fictional record,
repeats the import, and verifies that a user-edited synopsis, genre and note
survive. It stores complete synthetic subscription/rental/purchase observations
and their checked timestamp together in a single text field. A missing,
malformed or failed provider response preserves the previous observation. This
is a sequential fixture test: live TMDB, concurrent imports, and the YouTrack
adapter are not implemented. Task-wide notes are not per-user preferences.

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

The pinned `2026.2.19728` server container starts and serves the initial
configuration wizard at `http://localhost:18180/`. Database, configuration,
logs and backup directories are bind-mounted under `.cache/tracker-poc/`.
The wizard reached administrator password setup and was handed to the user; app
installation, API calls, workflows, UI and permissions have not been completed
or tested. Follow JetBrains' [installation guide](https://www.jetbrains.com/help/youtrack/server/youtrack-docker-installation.html)
to finish configuration and review the license; the initial wizard URL and
one-time token are shown in the container logs. No YouTrack score is justified.

## Outstanding

The complete comparison, equivalent applications, browser-level multiuser
preference isolation, live enrichment, browser demonstrations, equivalent YouTrack permission
tests, YouTrack setup and measurements, upgrade assessment, weighted scores,
and recommendation remain outstanding. Do not score or recommend either
product from the current evidence. Docker Desktop's external runtime storage
under `/var/lib/docker` was approved by the user on 2026-11-05.
