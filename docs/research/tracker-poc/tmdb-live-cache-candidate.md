# Seven-day live cache for the local POCs

The cache is enabled locally for **130 approved films** in each tracker.
Both bridges refreshed and returned the records through cache-only reads. An
aggregate comparison found matching metadata and availability status for all
130 films, including 109 matching complete provider sets and 21 unknown
observations in both. After a separate restart of each bridge, all 130 cache
entries remained readable. No tracker or Movary record was modified. The existing
noncommercial private-use assessment and its unresolved qualifications are in
[intended-use-20261031.md](../availability/intended-use-20261031.md); the
seven-day period is a conservative local choice, not a claim about TMDB's terms.

The two bridges retain their existing authentication and exact approved-ID
allowlist checks. Kaneo's cache read requires a visible task and obtains its ID
from the task's field; YouTrack's issue-scoped handler verifies issue visibility
and obtains the ID from its field. Cache-only reads never contact the provider.
Kaneo optionally accepts `FILMIQ_CATALOG_APPROVAL_DIR` for its local reviewed
catalog only. When unset, the catalog uses `FILMIQ_APPROVAL_DIR` as before; an
invalid configured catalog approval fails that catalog request closed. Cache
reads and live refreshes always use `FILMIQ_APPROVAL_DIR`, so a broader local
catalog approval cannot authorize additional provider requests.

Both deployed UI bundles report an explicit HTTP 401 or 403 from a
user-initiated metadata lookup as access denied and stop the active batch. They
ask the user to check sign-in, the film's lookup authorization and the provider
credential without
claiming which caused the denial; adding a film does not add its ID to the
approved set. A failed refresh preserves an earlier still-valid display, and
429 rate limits remain separate. YouTrack's Host API can conceal error status,
so an opaque failure remains generic; its batch still stops. The fictional
`ui/access_denied_workflow_check.mjs` exercises both adapters, batch stopping,
and the YouTrack single-film action. After the guarded update, the downloaded
YouTrack app package and served Kaneo bundle matched the prepared bytes; the
complete watched property, visible preferences, settings, usages and attachment
metadata were unchanged. These are readback and fictional-test results: no
real-film browser walkthrough or live 401/403 denial was performed.

The deployed bridges also correct an upstream authorization gap: a TMDB 401 or
403 previously became a generic 502 at both bridges, so a Kaneo batch could
continue making requests. Both bridges now return a sanitized 403,
the YouTrack issue handler forwards it without assuming which authorization
failed, and the shared UI message includes the provider credential among the
possible checks. Fictional adapter, issue-handler, batch and cache checks cover
denial propagation, stopping, no secret disclosure, and preservation of the
previous observation. The separate YouTrack bridge app was updated in place and
matched the prepared package; both existing processes restarted with their
checked configuration unchanged. Validated cache-only reads retained metadata
for all 130 approved films in each cache, with 109 complete availability
observations and 21 without a retained observation. The full main-app watched
property, preferences, settings, usages and checked attachment metadata were
unchanged. This verifies deployment and fictional behavior, not a live TMDB
denial or real-film browser workflow.

With caching enabled, Kaneo's explicit refresh is also task-scoped and the old
ID-only refresh route is disabled. With caching disabled, the existing ID-only
route remains unchanged: it requires a signed-in user and approved ID but does
not verify visibility of a task. It is suitable only for the existing
single-user POC assumption until that separate limitation is addressed.
The existing explicit refresh still invokes the provider; a successful response
is written to the cache and returned. A failed or partial response cannot
replace an earlier complete availability observation. There are no issue/task,
tracker-history, Movary, or preference writes in this path. An opt-in UI build
can hydrate via cache-only requests on reload; ordinary builds do not do so.
Although the JSON cache route never calls TMDB, rendering a cached poster URL
causes a separate request to `image.tmdb.org`. The opt-in UI fetches it using
`cache: 'no-store'`, renders a temporary object URL, revokes that URL on change
or unmount, and shows a placeholder if fetch or rendering is blocked. The
ordinary UI keeps its existing direct-image behavior. `no-store` controls the
browser HTTP cache; it does not remove previously stored images or prove that
browser temporary files, OS swap, or other copies cannot persist. The existing
authorization scope and image-retention assessment still apply.
Mounted cards start their transient poster fetch eagerly; the image element's
`loading="lazy"` attribute does not delay that preceding fetch.

## Intended local inventory

The single private root is `.cache/tracker-poc/private/tmdb-live-cache/`,
with **two independent** child directories `kaneo/` and `youtrack/`. Each child
would contain `policy.json`, `authority.json`, `cache/.cache-instance`, and
`cache/<id>.json` plus possible `.tmp` files. The authority records policy
decisions and film-ID purge watermarks, so it is private even though it contains
no film descriptions. Cache files include source metadata, availability and
poster paths; actual poster image bytes are fetched separately by the browser.
Existing browser-cached images and other independently retained copies still
need their own assessment and handling.

Use only one process for each child directory. Kaneo serializes its own threads;
YouTrack's current bridge serves one request at a time. There is no lock across
multiple processes. Configure both directories to be private to the service
user; the Docker bridge must be able to write only its dedicated child. The
`youtrack-tmdb-live-bridge/compose.cache.yaml` override supplies the optional
mount; it is not loaded by the normal Compose configuration.

For this candidate, **do not back up either cache or copy it into tracker
history, databases, exports, reports or screenshots**. The inventory is an
intended boundary, not verification that host backup software, browser caches,
or other tools actually exclude it. Other backup exclusions and the handling of pre-existing copies remain
unverified. Recovery fails closed if the latest
independently preserved authority is missing or mismatched. Restoring both a
cache and an outdated authority together cannot be detected; discard the
disposable cache on uncertain recovery instead of treating it as current.

On 2026-11-05 the empty intended root was created and a narrow Time Machine
exclusion for it was verified. Its existing private parent is included in a
configured Time Machine backup. After that check, the pilot initialized separate policies, and the collection
run stored 130 normalized cache records per tracker. A process-only check detected OneDrive
but did not establish its sync roots. Other backup/sync software and existing
browser caches remain unverified.

## Expiry and policy changes

Each metadata and availability observation is valid for at most seven days,
subject to an earlier policy expiry or termination. A fresh response does not
extend an earlier retained partial observation. Cache hydration returns the
earlier section expiry; opt-in UI builds discard the hydrated data at that
time; still-fresh metadata is then rehydrated using only the cache route. JSON
responses remain `no-store`; the separate poster request has its own cache mode.

The service rereads its policy file and verifies the authority on every cache
operation. Update the authority and policy consistently; while they differ,
the cache fails closed. On termination set the termination flag and record the
decision in the authority; simply setting `allowed` false blocks reads/writes
but is not the same as the termination purge. Stop the bridges while recording
and replacing the policy so no request races with the update. Already-rendered
browser data cannot be remotely recalled: close or reload open pages when a
decision is shortened or terminated. Earlier copied data needs its own purge.
An active, nonterminated policy marked `allowed=false` blocks maintenance as
well as reads and writes; it emits the generic maintenance failure and does not
delete retained files. Use the termination procedure when deletion is required.

Expired sections are purged on bridge startup, cache operations, and an hourly
in-process maintenance pass while that bridge is running. The maintenance pass
uses the same process-local lock as reads and writes; failures emit a generic
error without paths or film IDs. There is no worker when caching is disabled.
**Seven days is a display deadline, not a guarantee of physical deletion by
that exact time:** the next hourly pass can be almost an hour later, and an
error can delay it further. When the bridge is stopped, or the host is off, no
process can delete files; overdue data remains on disk until a later purge.
The project's existing [operations guidance](../../operations-recovery.md)
recommends the host's native scheduler; no separate schedule is registered
here. The running pilot requires manual log monitoring and a stopped-writer purge
when appropriate. No mechanism deletes data while the host is off; a prolonged
outage must be handled by the operator before the source deadline.

### Stopped-writer manual purge

Stop the corresponding bridge **and all other writers for that cache directory**
first. Confirm this operationally; the command does not inspect processes and
cannot prove the absence of a racing writer. With the worktree root as the
working directory, the following previews one directory and prints counts only:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_live_cache_purge.py \
  --directory "$PWD/.cache/tracker-poc/private/tmdb-live-cache/kaneo" --writers-stopped
```

Repeat with the `youtrack` child for that bridge. Add `--execute` to perform the
purge after the preview. Unresolved corrupt records are counted and return a
nonzero exit status; they are excluded from the affected record and section
counts. Investigate them separately without assuming they are expired. This
covers only the named cache and its authority, not browser copies,
backups, exports or other locations. The command does not contact TMDB.

### Renewing the policy window

The current authorization window ends December 6, 2026 UTC. Before renewing,
review the applicable source terms and the [POC use decision](tmdb-private-pilot-policy.md).
Renewal is a local operator decision; it does not grant new provider rights or
change the seven-day observation limit. A blocked or terminated policy cannot
be renewed by this command.

Stop both cache writers first, from the worktree root. The Kaneo command stops
only its recorded bridge and refuses an unrecognized listener:

```sh
.venv/bin/python docs/research/tracker-poc/kaneo_live_pilot.py --stop
docker stop film-iq-tracker-poc-tmdb-live-bridge-1
```

Preview each cache separately; `--days` is an explicit new window of 1–30 days.
The preview does not write, contact TMDb, or reveal film identifiers:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_live_cache_renew.py \
  --directory "$PWD/.cache/tracker-poc/private/tmdb-live-cache/kaneo" --days 30 --writers-stopped
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_live_cache_renew.py \
  --directory "$PWD/.cache/tracker-poc/private/tmdb-live-cache/youtrack" --days 30 --writers-stopped
```

Add `--execute` to each command to record the renewed authority and policy.
The new deadline must be later than the current one. Existing cached sections
keep their original deadlines, including after renewal; if those deadlines have
passed, a bridge's startup cleanup removes the expired sections. This command
does not fetch replacement data. Stop if either execution fails: leave both
bridges stopped and inspect the local authority and policy before restarting,
because an interrupted update can leave them mismatched. Never restore an older
authority alongside a newer cache. After both renewals succeed, start the
bridges using the [local runbook](local-runbook.md).

### Rolling back an older cache reader

The current reader can store unknown availability attempts with their attempt
times. Earlier readers reject those sections. Before starting an older reader,
stop every writer for the affected cache and, while the current code is still
checked out, preview the compatibility conversion:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_live_cache_downgrade.py \
  --directory "$PWD/.cache/tracker-poc/private/tmdb-live-cache/kaneo" --writers-stopped
```

Repeat with the `youtrack` child. Add `--execute` after reviewing the count.
The conversion removes only unknown availability sections and their attempt
timestamps; it keeps metadata, complete/partial observations and authority
unchanged. If either command fails, keep that writer stopped and inspect its
cache before rollback. No provider or tracker request is made.

## Review and verification

The collection run uses the reviewed policy and independently initialized
authorities described above. Other backup/sync coverage, pre-existing browser
copies, and the offline physical-deletion limitation remain open. Reassess
these boundaries and source use before expanding beyond the authorized set. Both bridges and the
UI require deliberate configuration and the updated YouTrack issue handler
before cache hydration can work. `FILMIQ_TMDB_CACHE_ENABLE=1` and
`FILMIQ_TMDB_CACHE_DIRECTORY` are explicit server opt-ins. The UI build flag
`__FILMIQ_LIVE_CACHE__=true` is separate; `build_youtrack.py
--live-cache-candidate` creates a separate review package and does not install
it. Neither option initializes storage. A YouTrack override also requires
`FILMIQ_YOUTRACK_CACHE_DIR` pointing to its dedicated child.

Fictional-only checks:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc/youtrack-tmdb-live-bridge:docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_live_cache_check.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_live_cache_maintenance_check.py
node docs/research/tracker-poc/youtrack-tmdb-live-bridge/metadata_check.cjs
node docs/research/tracker-poc/ui/live_cache_ui_check.mjs
(cd docs/research/tracker-poc/ui && node poster_check.mjs)
```

On 2026-11-05, 130 sequential fictional in-process reads, each performing a
whole-directory purge scan, took 2.665 seconds (20.50 ms/read) on this local
host; this excludes HTTP and browser overhead and is not a production scale
claim. No benchmark contacted TMDB or used personal records.

Fictional browser checks were run in the actual Kaneo UI and restricted-user
YouTrack iframe. For both, metadata and PNG bytes were intercepted locally;
the initial fictional availability expired, a cache-only reread restored the
still-fresh synopsis with availability unknown, and no live refresh occurred.
Each browser rendered the synthetic poster through a blob URL after a `no-store`
fetch and revoked the prior blob on expiry. The YouTrack test used the separate
fixture-gated app, never the installed live app. The test proves those UI and
iframe behaviors with intercepted responses, not the live cache endpoint or
real images. An independently authorized real-image HEAD check established
HTTP 200, no redirect, and `Access-Control-Allow-Origin: *` for both local
origins; it did not verify all future responses or removal of old cached copies.

To repeat the browser tests, first build the opt-in Kaneo bundle and prepare the
separate fixture-gated YouTrack app as described in
[`cache-fixture/README.md`](cache-fixture/README.md). The installed test widget
must be compiled with both `__FILMIQ_CACHE_FIXTURE__=true` and
`__FILMIQ_LIVE_CACHE__=true` for this check. Use only an existing fictional
FILMPOC issue titled `Fictional film` with fixture ID `900000001` and a fictional
Kaneo task with the same fixture identity. The checks need the local trackers,
the existing fictional sessions and project-local browser tooling. They block
external and FILMREAL requests and intercept metadata and poster bytes:

```sh
docs/research/tracker-poc/ui/node_modules/.bin/esbuild docs/research/tracker-poc/ui/src.jsx \
  --bundle --minify --loader:.js=jsx --define:__FILMIQ_LIVE_CACHE__=true \
  --outfile=.cache/tracker-poc/kaneo-live-cache-candidate.js
docs/research/tracker-poc/ui/node_modules/.bin/esbuild docs/research/tracker-poc/ui/youtrack.jsx \
  --bundle --minify --format=esm --define:__FILMIQ_CACHE_FIXTURE__=true \
  --define:__FILMIQ_LIVE_CACHE__=true \
  --outfile=.cache/tracker-poc/youtrack-cache-fixture-app/widgets/films/app.js
# Upload only the separate fictional app directory with the official YouTrack CLI.
node docs/research/tracker-poc/ui/live_cache_browser_check.cjs kaneo FICTIONAL_TASK_ID FICTIONAL_PROJECT_ID PROJECT_LOCAL_FICTIONAL_COOKIE_FILE
node docs/research/tracker-poc/ui/live_cache_browser_check.cjs youtrack FILMPOC_ISSUE_ID
```

No actual source credential, real film ID or provider response is needed for
these checks. The YouTrack browser check requires a preexisting signed-in
fictional test profile in the ignored project cache; it does not sign in using
the user's active browser session.
