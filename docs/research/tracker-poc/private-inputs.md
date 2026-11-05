# Private film inputs for the tracker experiments

These inputs are for the local POCs only. Keep the generated files in the
project's ignored private cache. Do not commit personal history or use this
process to alter Movary. Movary remains authoritative for watched history,
ratings and the intentional watchlist.

Refresh a **separate POC snapshot** through the supported read-only workflow in
[personal refresh](../../usage/personal-refresh.md); do not overwrite the live
FilmIQ snapshot. Generate a discovery JSON report against that same snapshot,
the active evidence database and selected accepted cohorts using the documented
[discovery command](../../usage/discovery-report.md). Its refresh timestamp must
match the successful snapshot status. Missing, stale or mismatched inputs fail.

For example, after those two inputs have been prepared:

```sh
uv run python docs/research/tracker-poc/prepare_private_films.py \
  --snapshot .cache/tracker-poc/private/movary-snapshot.json \
  --report .cache/tracker-poc/private/discovery.json \
  --output .cache/tracker-poc/private/film-input.json
uv run python docs/research/tracker-poc/prepare_private_films_check.py
```

The output combines accepted reviewed unwatched discoveries with watched Movary
records, using only exact positive TMDB IDs. Unresolved history remains separate.
Duplicate or contradictory identities fail rather than silently disappear. The
output omits personal ratings, notes, and Movary watchlist state. A missing watched
date stays unknown. The original accepted source-list URLs and their provenance
are preserved as evidence links; a list or ballot is not automatically a review.

Discovery titles, source years and director names are source-listed assertions.
They are not necessarily verified release metadata; canonical `release_year`
remains unknown here. Watched-film titles come from Movary's API or native exports,
whose upstream catalog origin and applicable retention terms are not established
by this export. Existing source restrictions and retention deadlines continue to
apply; deriving this input does not extend them. No TMDB display-catalog facts,
posters, or review text are copied into the manifest.

## Kaneo importer

`kaneo_private_import.py` accepts this private manifest and creates missing film
tasks in an explicitly selected local POC project using the test account's
session. Film identity and initial fields are submitted in the same task create
request. Each rerun checks for duplicate identifiers and leaves existing tasks
completely untouched, including their descriptions, evidence and lifecycle
states. Run only one importer at a time: the tracker does not enforce uniqueness
of these custom-field values. A failed run can be retried sequentially.

The tracker fields are `POC TMDB ID`, `POC Identity Provenance`, `POC Field
Provenance`, `POC Source Year`, `POC Source Director`, and `POC Evidence`. They hold supplied identities,
source assertions and links; they do not establish a verified release year or
catalog metadata. Watched history remains in the separate private Movary inputs,
keyed by TMDB ID. No real personal preference data is written to tracker fields
or to the synthetic preference bridge.

Before using actual input, run the fictional-only live test:

```sh
uv run python docs/research/tracker-poc/kaneo_private_import_check.py \
  --directory .cache/tracker-poc
```

It exercises creation, an unchanged retry, preserved user edits/lifecycle,
duplicate input rejection, and a simulated lost response after server-side
creation. It creates a separate synthetic project and retains its test tasks.
It does not establish concurrent-import safety. The importer is deliberately
separate from a future enrichment update path: it does not overwrite an existing
film when source metadata or links change.

On 2026-11-05, `kaneo_private_setup.py` created a separate non-public local
workspace and checked that an unrelated signed-in synthetic viewer was denied
access. The user-authorized private import created 130 records; a sequential
retry created zero. `kaneo_private_verify.py` read back all 130 distinct IDs,
field provenance and evidence, and reconfirmed viewer denial against an imported
record. No watched state, ratings, personal notes or watchlist status were written
to Kaneo. Per-user watched-state integration remains a separate unfinished step.

`kaneo_movary_mapping.py` prepares a separate, project-bound sidecar for the
authenticated POC user from a complete Movary snapshot. The source is explicitly
labelled `Movary` and the successful refresh time is retained. Played-API dates
and exact play counts remain separate from history-export rows, so repeated plays
and unknown dates are not converted into invented timestamps or double-counted
across sources. This sidecar does not write tracker records, the editable
preference database, Movary, ratings, personal comments or watchlist state.
It rejects an older observation for a user rather than replacing newer history.
The fictional-only `kaneo_movary_mapping_check.py` verifies the mapping logic;
project authorization and user-isolation tests must also pass before exposing
any personal sidecar via the preference bridge. On 2026-11-05, after those
synthetic tests passed, a user-authorized local refresh mapped 27 watched works
to the synthetic POC user. An unchanged rerun produced identical sidecar contents.
