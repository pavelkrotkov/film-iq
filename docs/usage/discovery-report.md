# First-use private discovery report

Discovery needs no personal ratings, budget, schedule or viewing-plan declaration.
Both score fields may remain null. A supplied fresh complete history snapshot
supports watched exclusion independently of ratings; without it, source evidence
is still reported and watched status stays unknown. Historical live-rating/edit
acceptance requests below are optional evidence gaps, not release prerequisites.

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

Source order remains available explicitly with `--order source`; the default
public-support ordering is described below. Neither ordering is fitted personal
ranking or a claim of complete publisher/year coverage. Retain private factual inputs
only under each source's recorded permission; no broader scrape is implied.

## Readable output

The Markdown output now starts with a readable film shortlist: title, source
listed year/director, original critic reasons and reviewed film links. Watching
choices and retained personal history follow; detailed source/audit fields are
in a separate expandable section. A pick supported by multiple supplied source
ballots lists every supplied reason rather than duplicating the film. JSON
retains all machine-readable fields. Film years and director names remain raw
source assertions, so a catalog spelling or premiere-year correction does not
silently rewrite the published source.

## Reviewed display facts and transparent ordering

`discover` accepts an optional `--catalog path.json` containing a finite,
explicitly reviewed display snapshot. It does not fetch metadata or change the
evidence database. Catalog aliases, director names, runtime and release date are
shown only for already reviewed matching TMDB identities. Original source
title/director/year, rank, lineage and all personal scores remain unchanged in
JSON and evidence details. Catalog release dates are labeled separately from
source-listed/eligibility years; a later commercial release never rewrites the
source's year. Expired or future metadata falls back to original source facts.

The snapshot schema is `version: "reviewed-display-v1"`, timezone-aware
`observed_at`/`expires_at`, nonblank `attribution`, and a `records` array. Each
record supplies positive `tmdb_id`, nonblank `title`/`original_title`, nonempty
`directors`, nullable ISO `release_date`, nullable positive `runtime_minutes`,
nonblank `reviewer` and nonempty factual `evidence` links. Duplicate IDs fail.
Expiry must be after observation and no later than180days. Only these display
fields are retained; synopsis/images or arbitrary provider fields are ignored.
This provenance is an explicit review assertion, not independent quality proof.

The CLI defaults explicitly to `--order public-support`: existing C3 reviewed
evidence-group count only, decreasing; ties retain source order. Published ranks
remain separate source reasons. Unknown support keeps its original source-order
slot rather than becoming zero or being pushed below assessed films. This is a
provisional public-support baseline, not a calibrated quality or enjoyment model,
and source exposure/missingness remain unknown where unmeasured. Use
`--order source` to restore the selected ballot/input order. Direct Python
`discovery_command`/`run_once` calls retain their source-order default.

The scheduled `film_iq.operations` command accepts the same optional `--catalog`
and explicit `--order` choices/default. These are report options, never forwarded
to personal export/refresh commands. Retain display snapshots privately under
their recorded attribution/expiry and the source/provider terms; no new provider
feed, model, purchase, watchlist write or web interface is introduced.

## Permitted local offer observations

With an explicit evidence database, discovery automatically includes retained
US offer observations already imported under a registered allowed source policy.
No extra flag, provider selection, personal plan or live request is required.
A database with no permitted matching observations keeps the existing unknown
access output. Only reviewed film identities receive offer details.

Cards distinguish earlier reported options from an incomplete/inconclusive latest
check, with source, checked date and service links. Complete unknown-tier claims
and partial positive claims remain exploratory; an unsuccessful check never
removes or refreshes the prior comparable snapshot. JSON and the collapsed audit
retain both states, all price/quality/add-on/cut variants, unknowns, original
source times and registered display attribution. Private rights-review notes are
not exposed. Report exports inherit source permissions and retention deadlines.

Future observations and denied, expired or terminated retention policies are
hidden before presentation. These are source claims, not verified access,
account entitlement or purchase advice; recheck applicable price/tier/expiry with
the service. This bridge does not acquire data, grant rights, adopt a provider,
configure polling or bypass B4/B8.

Each linked claim shows its own source-check time. The enclosing batch/attempt
record time is labelled separately: importing cached assertions in a newer batch
does not refresh their source timestamps or retention deadlines. Mixed-age
claims retain their distinct times in both the card and detailed audit.
