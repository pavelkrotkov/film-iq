# Newer Movary watched observations

This is an installed, manually invoked POC, not a scheduled job.
`youtrack_watched_refresh_proposal.py` builds a pure preview;
`youtrack_watched_refresh.py` adds a dry-run-first importer and an explicit
`--apply` path for the v3 app's `/refresh` endpoint. The v2 importer remains
a same-observation migration only. No real
snapshot, YouTrack record, Movary data, browser session or network service is
used by the fictional tests.

The proposal consumes a newer successful Movary snapshot and its matching
non-stale status, three API collections and a history export. It reuses the
existing snapshot mapping, derives watched membership from the API and export
provenance, and stops if the derived and reported watched sets disagree. It
requires every watched ID to match exactly one current FILMREAL issue ID and
stops on missing, duplicate or malformed identities, unresolved history,
unavailable prior issues or non-increasing observation times. Source IDs are
supplied mappings, not independently verified film identities.

Current source events appear under the new observation time. Older unbound
entries and prior bound entries that changed, disappeared or no longer match
their issue are retained separately with their original issue, timestamp and
events. Current and historical evidence can therefore coexist for one issue;
historical unbound events do not establish that issue's current watched status.
Existing historical entries survive another proposal. A complete source can
still reflect edits between its API and export reads, and a manually supplied
CSV's completeness is operator-asserted, as described in the
[personal refresh documentation](../../usage/personal-refresh.md).

The candidate app stores current and historical entries in a v3 snapshot. Its
handler independently validates the full stored property and checks access to
all its current and historical issues before a write; the visibility-filtered
GET alone cannot establish that completeness. It derives old history from the
stored property instead of accepting it from the client, rejects newer imports
that bypass `/refresh`, and makes an identical v3 retry a no-op. The importer
validates source provenance, but the handler itself can only validate the
caller's completeness assertion; it cannot independently verify Movary's export.

Old handlers cannot read v3 data. The candidate `restore-legacy` endpoint
rejects conversion when historical entries exist, because v1 cannot represent
them. If history is empty, conversion is possible but drops identity bindings;
it is not a lossless rollback. Every stored project must be compatible before
downgrading the handler, and removing or renaming an app property can delete
app-owned data. The handler passed a live test in a separate fictional YouTrack
app, including mixed v2-to-v3 refresh, original history timestamps, retry and
refusal of a lossy downgrade. Hidden-existing-entry rejection remains an
offline check. The FilmIQ app was updated in place with this handler and UI;
the existing watched projections, visible preferences, app settings and usages
matched before and after. These pre-update project projections did
not constitute a full-property backup.

A separately authorized read-only Movary refresh later produced a new
owner-only project-local snapshot. Its 27 watched IDs and event arrays matched
the prior source observation, and the new importer preview proposed 27 current
films with 11 prior historical entries. After an exact full-property export,
the reviewed single-writer procedure applied this observation once. Readback
confirmed 27 current entries and 11 prior unbound entries retained separately
with their original observation times. The original and newer source IDs and
ordered event arrays matched; other projects and legacy-empty state in the
property, visible preferences, and app settings/usages were unchanged. The
pre-refresh export and the verified post-refresh export remain owner-only in
the project-local private cache. The post-refresh full-property comparison was
semantic JSON equality; the pre-refresh export preserves the raw property.

This is supporting continuity evidence, not independent account or
film-identity verification. The earlier 11 unbound entries remain historical
evidence rather than proof of the identities of those earlier issues. No
Movary, issue or watchlist writes were made during this refresh. Full server
disaster recovery has not been demonstrated. See the
[watched-property recovery notes](watched-property-backup.md); stop other
property writers during export and refresh because atomic concurrent
compare-and-swap has not been established.

To preview a newer complete project-local snapshot after obtaining it through
the [read-only Movary refresh workflow](../../usage/personal-refresh.md), run:

```sh
UV_CACHE_DIR="$PWD/.cache/tracker-poc/uv-cache" uv run --no-sync python \
  docs/research/tracker-poc/youtrack_watched_refresh.py \
  --snapshot .cache/epic-c/personal/snapshot.json
```

The path is an example; use the actual snapshot with its adjacent `.status`
file. The command reports aggregate counts and does not write. `--apply`
submits the validated observation to the local app and verifies readback; it
does not run the Movary refresh or write to Movary. A presence-only check found
the existing project-root credential configuration. A later read-only refresh
using those credentials and exporters succeeded; no automatic schedule was
installed. Do not treat an old snapshot as a new observation.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/youtrack_watched_refresh_proposal_check.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/youtrack_watched_refresh_vertical_check.py
node docs/research/tracker-poc/youtrack-app/tests/movary_check.cjs
```

The fictional check covers a prior unbound entry alongside a new direct-ID
observation for the same issue, changed and removed mappings, repeat refresh,
API-history-only and CSV-only films, inconsistent source membership, stale or
incomplete input, duplicate and missing issue IDs, malformed dates, and input
preservation. The vertical check connects the actual Python importer to the
actual JavaScript handler in a fictional mock context: preview, apply, retry,
incomplete-source rejection and hidden-stored-entry rejection. It does not
exercise a live Movary refresh or the real FilmIQ app update.
