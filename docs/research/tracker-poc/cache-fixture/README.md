# Offline fictional cache integration

This opt-in experiment compiles the existing Kaneo and YouTrack film UIs in a
fictional-only mode. It reads two invented records from the project-local cache
and uses the trackers for their actual record data. **It does not implement or
validate persistence of real TMDB data or the real-data enrichment path.** The
synthetic IDs, titles, synopsis, and services are fixtures, not TMDB responses.
No API key or provider calls are used. The mode disables Movary and personal
preferences, and intentionally shows only fixture IDs 900000001 and 900000002.

The Kaneo bridge checks the actual session, reads the requested task using that
session, verifies its configured fictional project and its fixture ID, and only
then reads the cache. The YouTrack route uses the existing separately installed
`filmiq-tmdb-fixture-isolated` issue handler: that handler checks caller, issue
visibility, project `FILMPOC`, and ID before requesting the local cache service.
Both services bind loopback. The YouTrack fixture container shares YouTrack's
network namespace, and therefore is not a production isolation boundary.

## Setup

The following assumes the pinned tracker instances and prerequisites in the
parent POC README, including installed Node dependencies, a dedicated fictional
Kaneo project, a fictional Kaneo user with access, and the existing separately
installed/configured `filmiq-tmdb-fixture-isolated` app attached to FILMPOC.
See `../youtrack-tmdb-bridge-poc/README.md` for that handler's installation and
settings. Do not apply these fixture settings to the live app.

1. Create a task titled `Fictional film` in the fictional Kaneo project with
   text custom field `POC TMDB ID` equal to `900000001`. Create or select a
   FILMPOC issue with the exact same title and integer `FilmIQ TMDB ID` equal to
   `900000001`. Only use synthetic records. The UI's exact-title check will not
   display fixture metadata on differently titled records.
2. Build with the fictional project ID supplied explicitly:

   ```sh
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc/cache-fixture:docs/research/tracker-poc:src \
     .venv/bin/python docs/research/tracker-poc/cache-fixture/build.py --project FICTIONAL_PROJECT_ID
   ```

   This initializes `.cache/tracker-poc/fictional-cache` only if absent and does
   not overwrite it on subsequent builds. Its cache policy is **fictional** and
   expires 2027-01-01 UTC. The cache and authority contain only fictional IDs;
   they are made readable by the unprivileged fixture container. Do not put real
   records or credentials there. Offline expiry/purge is not automated.
3. Start the Kaneo fixture bridge, supplying the same fictional project ID:

   ```sh
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc/cache-fixture:docs/research/tracker-poc:src \
     .venv/bin/python docs/research/tracker-poc/cache-fixture/kaneo_bridge.py \
     --project FICTIONAL_PROJECT_ID --cache-directory .cache/tracker-poc/fictional-cache
   ```

   With the existing static server on `localhost:15174`, sign in as the
   fictional user and open `http://localhost:15174/dist/cache-fixture/`.
4. Stop the older synthetic provider service if it occupies port 15176 inside
   YouTrack's namespace, then start only the cache fixture service:

   ```sh
   docker compose -f docs/research/tracker-poc/compose.yaml \
     -f docs/research/tracker-poc/cache-fixture/compose.yaml \
     --profile tmdb-cache-fixture up -d --no-deps --no-recreate --pull never tmdb-cache-fixture
   ```

   Install the separate generated `.cache/tracker-poc/youtrack-cache-fixture-app.zip`
   as `filmiq-cache-fixture-ui`, leaving `filmiq-poc` and the live bridge
   installed. Open `http://localhost:18180/app/filmiq-cache-fixture-ui/films`.
   Cache misses and expiry do not invoke a provider.

## Checks and observed evidence

The fixture-only cache, cache miss, expiry, incomplete availability preservation,
and simulated authorization failures can be checked without network access:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc/cache-fixture:docs/research/tracker-poc/youtrack-tmdb-bridge-poc:docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/cache-fixture/check.py
```

The following browser checks **edit the fictional record's synopsis**, so give
only the fictional task and issue IDs and the project-local fictional user's
Netscape cookie file. They use separate headless Brave profiles and block
non-local requests, Movary, and FILMREAL. The YouTrack check additionally
expects the existing fictional account/profile and admin integration token in
the project's ignored POC cache; it checks the issue identity before editing.
They require the matching servers and app to be running.

```sh
node docs/research/tracker-poc/cache-fixture/browser_kaneo.cjs FICTIONAL_TASK_ID PROJECT_LOCAL_FICTIONAL_COOKIE_FILE
node docs/research/tracker-poc/cache-fixture/browser_youtrack.cjs FILMPOC_ISSUE_ID
```

On 2026-11-05 both existing UI builds were exercised against the local pinned
trackers: a fictional synopsis saved to the tracker and survived reload, and
the fictional subscription offer reappeared after a fresh cache read on reload.
Both tracker endpoints returned the fixture after their bridge processes were
restarted, and rejected anonymous reads. The offline check simulates a partial
observation and cache miss and verifies previous complete availability is
preserved; it does not simulate a live provider failure. Normal UI bundles and
live apps were not replaced. The initial separate-widget installation lacked a
before/after watched snapshot hash; a later fixture-widget update had an
unchanged hash, and the existing 27-film watched readback was separately
compared with its imported source snapshot. These tests do not establish
multi-user isolation, live-provider retention rights, or production operation.
