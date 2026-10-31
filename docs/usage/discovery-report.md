# First-use private discovery report

Use `film-iq discover` for a bounded read-only multi-film report. It joins a
complete curated-import preview with the current accepted revision and reviewed
TMDB matches in SQLite, then optionally joins a private Movary snapshot. It does
not mutate Movary, create watchlist entries, buy access, send alerts or start jobs.

Run inside the selected project folder, with source permission recorded in the
curated manifest before importing:

```sh
uv run film-iq import-list --csv .cache/curated.csv --manifest .cache/curated.json \
  --persist data/evidence.db > .cache/curated-preview.json
uv run film-iq discover --cohort .cache/curated-preview.json --database data/evidence.db \
  --snapshot data/personal.json --format markdown > .cache/discovery.md
uv run film-iq acquisition-status --database data/evidence.db
```

Import remains pending until an independent `AuditAttestation` is explicitly
accepted through the existing extraction-acceptance API. The report checks
`current_extraction` and current matches rather than trusting preview status;
a stale/obsolete revision stays pending. Without `--database`, all entries stay
pending. Unknown identities remain visible and never enter suggested picks.

The `refresh-movary` CLI alias delegates to the same complete read-only exporter
workflow described in [personal refresh](personal-refresh.md). Personal comments
and raw API/export provenance are excluded from report output. Enjoyment, the
user's artistic merit and external critical recognition remain separate fields.
Conflicting merit stays null/review. Watched films remain in the evidence table
with their scores, but are excluded from the suggested-unwatched list.

Omit `--snapshot` to show personal state as unknown. Missing/stale refresh status
also suppresses suggested picks, while retaining visible review data. Rated-only
films keep empty/unknown watched dates. Source facts and ranks come from accepted
stored observations; changing the preview cannot change accepted published ranks.

No-purchase/no-service is always shown. This first-use report has no verified
rental/streaming input, so access, price, entitlement and access freshness remain
unknown rather than invented. Existing provider/planner POC reports remain under
`film-iq report`. No HTTP interface or background alert system is introduced.

Reports contain private scores and potentially private-study source facts. Keep
them in ignored private storage; source permission does not imply redistribution
permission. The initial real ten-candidate report has accepted source entries,
three reviewed identities and seven unresolved works, but no genuine personal
snapshot was supplied: personal refresh remains unknown and it suggests no films.
Real-user watches/ratings and changed/deleted enjoyment/merit readback acceptance
remain open; synthetic tests do not satisfy those live requirements.

The subsequently authorized live-refresh check completed and generated a separate
private `discovery-live.json`/`.md` report using the matching complete personal
snapshot/status. The earlier first-use report remains historical. Private
account contents and counts are deliberately absent from public documentation;
the live check does not establish the outstanding nonempty-rating, merit-change
or real-user acceptance cases. See the personal-refresh follow-up.

## Multiple selected ballots

Repeat `--cohort` to discover films across separately imported ballots in the
same evidence database:

```sh
uv run film-iq discover --cohort data/first-preview.json --cohort data/second-preview.json --database data/evidence.db --snapshot data/personal.json
```

Every ballot still needs its own complete source/identity audit and explicit
acceptance. Combining previews never grants acceptance. The report retains all
source observations, each ballot's scope/counts, and global dependence-aware
recognition. A reviewed unwatched work appears once in suggestions with all
selected source reasons. Candidate, accepted, unresolved and watched-excluded
counts describe source observations; `unique_films` counts distinct reviewed
work IDs, and `cohort_count` counts selected ballots. Unresolved entries cannot
be safely deduplicated by title. Duplicate revision inputs are rejected.

Selection order determines shortlist order; this is not a fitted personal ranking
or a claim of complete publisher/year coverage. Retain private factual inputs
only under each source's recorded permission; no broader scrape is implied.
