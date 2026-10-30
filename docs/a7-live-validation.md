# A7 live validation — 2026-10-30

The saved Movary token was loaded from the selected project's ignored, mode-0600
`.env`. No credential value was printed, committed or copied into this report.
Browser automation was not used for these integration checks.

| Check | Observed result |
| --- | --- |
| `GET /api/v1/authentication/token` | HTTP 200 |
| Implemented paginated played reader | Complete, 0 records |
| Implemented paginated history reader | Complete, 0 records |
| Implemented paginated watchlist reader | Complete: 0 before approval, 1 after the selected addition |
| Supported ratings CLI and atomic snapshot adapter | Two validated identical header-only exports, 0 ratings |
| Implemented movie-search read for the candidate | Initial HTTP 500; complete after the approved configuration fix |

The installed application log reports `TMDB API key is probably not set or
invalid.` Its `TmdbClient.php` maps an upstream HTTP 401 to that exception.
This distinguishes a TMDB authorization failure from a Movary-token failure or
network timeout. Raw application logs and credential-bearing requests were not
retained. The user subsequently supplied a valid TMDB v3 key: direct TMDB
authentication, film details/credits and US watch-provider requests succeeded.
Automatic approval review initially rejected transferring the key to Hermes and
recreating the service without explicit authorization. The user then explicitly
approved both proposed actions. The saved key was applied to the existing
deployment and only the existing service was recreated, with image pulls disabled.
[The configuration result](a7-live-configuration-result.json) records a healthy,
running `leepeuker/movary:0.82.1` service and mode-0600 secret file. Both the
selected-film search and original failed NBR search now complete through Movary.

The [independent primary-selection audit](a7-primary-selection.json) verifies
one original NBR 2023 Best Film award. It is a categorical award with no numeric
rank; the award edition is not substituted for an unstated film release year.
The one-record scope excludes all other announcement categories. Only factual
metadata and links are retained; the record hash is not a publisher HTML hash.
This initial candidate has paid offers and is not selected for the zero-purchase
scenario; its local identity remains unresolved and it contributes no score.

That factual record was persisted and explicitly accepted through the existing
ingestion/audit interfaces in a private ignored local evidence database. An
unchanged ingestion produced zero new database changes. The original NBR source
and lineage are explicit; no derivative Wikipedia vote was promoted.

## Completed read-only selected-film trace

The [second independent primary audit](a7-bicycle-selection.json) verifies
*Bicycle Thieves* at **=20** in BFI's 2022 directors' aggregate, with Vittorio De
Sica and 1948. The aggregate and film-specific BFI record corroborate one fact,
not two independent votes. Publication date remains unknown.

Direct TMDB film details/credits return ID **5156**, English title
*Bicycle Thieves*, original title *Ladri di biciclette*, 1948, Vittorio De Sica,
and **89 minutes**. The persisted title-only observation initially abstains;
an explicitly labelled automated operator review records the API-supported
identity without rewriting the raw observation. This live POC is separate from
the unchanged held-out evaluation; no auto-match precision claim follows.

The actual A1 scorer returns one independent group and reciprocal-rank component
**1/20**, preserving the tie and partial aggregate scope. Unchanged ingestion
and automatic-decision replay produce zero new database changes. The actual
read-only report command leaves the database dump unchanged.

The [real report](a7-real-report.md) includes the default CLI result plus a
separately calculated, configured Tubi-only scenario through the existing planner.
The [selected-plan record](a7-real-selected-plan.json) preserves the exact result:
one film, **89 of 90 configured minutes**, **USD 0 incremental purchase cost**,
Tubi TV **ads**, entitlement **unconfirmed**, configured slot **2026-11-01**.
The default CLI may also choose a conditional library offer; the selected scenario
does not assume library eligibility. Full observed US offers remain intact in
the private JSON report and cached response slice. No rental or subscription
price is supplied or invented. Actual playback is unverified; no calendar
commitment is created.

The source is TMDB / JustWatch, with the returned TMDB provider-information link.
[TMDB's endpoint documentation](https://developer.themoviedb.org/reference/movie-watch-providers)
requires JustWatch attribution and explains that this is provider information,
not full content deep links. Only minimal facts and a single-film US response
slice are retained in the ignored project cache; no catalog dump or provider
images are published. Full API terms were not accessible to the web reader;
release/commercial retention compliance is not established by this local POC.

Re-render the default report from the prepared local snapshot without network
or credentials:

```sh
PYTHONPATH=src ../a4/.venv/bin/python -m film_iq.cli report \
  --database .cache/epic-a-live/evidence.db \
  --inputs .cache/epic-a-live/report-inputs.json
```

The configured Tubi alternative is a separate call to the existing `compare`
planner with the same scored film and the observed provider 73 `ads` offer,
one slot, 90 minutes, one film, zero budget and no assumed current subscriptions.
It is not a filtered response passed off as a complete API capture.

## Approved live operations and observed result

The user explicitly approved both of the following operations before execution:

1. Configure the documented Hermes Movary deployment with the existing saved
   TMDB key: set `TMDB_API_KEY` in its existing `.env`, reference it in the
   existing Compose service environment, validate Compose, and recreate only
   `movary` using the same locally installed `leepeuker/movary:0.82.1` image.
   This persists the secret on Hermes and briefly restarts that service.
2. Execute this exact existing dry-run result through the API:

   ```text
   Preview: add Bicycle Thieves (TMDB 5156) to watchlist
   ```

   Add the Movary catalog movie first only if absent, then add its watchlist
   entry if absent, read back the result, and retry to check idempotence.

[The actual CLI/API trace](a7-live-write-result.json) completed at
2026-10-30T11:59:59.939518+00:00. The initial lookup found no catalog movie or
watchlist entry. The real CLI, with `--execute --approve`, issued:

1. Complete movie search: HTTP 200.
2. `POST /api/v1/movies/add`: HTTP 200.
3. Complete watchlist read: HTTP 200.
4. `POST /api/v1/users/{username}/watchlist/movies`: HTTP 204.

The CLI returned `added to watchlist` in **0.459 seconds**. API readback found
TMDB **5156** exactly once, mapped to distinct Movary ID **1**. The existing
watchlist was preserved. Repeating the exact CLI returned `already on watchlist`
in **0.175 seconds**, with **two GET requests, zero POST requests**, and an
unchanged watchlist. These are single-run observations, not latency benchmarks.
Afterward, complete reads returned played 0, history 0 and watchlist 1. No direct
Movary database writes or personal rating changes were performed. No production
code, dependency or Movary fork was needed for this configuration fix.

[The live ratings result](a7-live-ratings-result.json) also exercises the actual
`export_ratings`/`read_ratings` adapter: two supported CLI streams pass validation
and atomic local replacement, producing identical 36-byte header-only CSVs in
2.017 seconds total. The mode-0600 snapshot and temporary output stay in the
ignored project cache; no remote export copy or personal CSV is committed.

## Gate A decision

Accept the narrow POC: original critical fact → explicit audited observation →
reviewed TMDB identity → sourced public score → classified US offer → configured
feasible/no-purchase report → preview → user-approved API write → authoritative
readback and idempotent retry. The integrated credential-free fixtures exercise
rank/tie/unranked/partial semantics, rated-only/deleted-rating replacement,
ambiguous/reversible identity, failure/unknown behavior and full synthetic replay.
The actual empty ratings export verifies the installed exporter/schema, not a
nonempty live rated-only or deleted-rating example; those remain fixture-backed.
No personal test rating was invented to manufacture that evidence.

| Gate A requirement | Acceptance evidence |
| --- | --- |
| Source semantics and completeness | Four licensed page captures, 42 independently audited records, contrasting adapters and partial/ambiguous fixtures; one separately scoped original BFI fact in the live trace |
| Movary reads including rated-only semantics | Complete real API reads and installed ratings export; nonempty rated-only and deleted-rating replacement exercised by deterministic fixtures |
| Idempotence and failed-request safety | Ingestion/automatic replay adds zero changes; actual CLI retry makes zero POSTs; failure fixtures preserve unknown instead of inferring absence; initial failed search caused no personal write |
| Explicit selected approval | User approved the displayed TMDB 5156 preview; catalog creation preceded watchlist insertion; authoritative readback contains the target exactly once |
| Sourced report and no-purchase option | Original =20, reviewed identity, real US ads offer, configured 89-minute/zero-purchase scenario; unknown entitlement/playback and prices stay explicit |
| Measured findings and dependency discipline | Recorded HTTP statuses, failure/fix, single-run CLI timings, preserved source/identity evidence, quality checks and ADR notes; no new runtime dependency or provider-choice promotion |

This is a POC acceptance, not release readiness. Playback, personal entitlement,
recommendation satisfaction, population identity precision, calibration, broad
source/provider coverage, commercial rights/retention and deployment restore
remain unverified. The four-case held-out identity run still has zero automatic
accepts and undefined precision. The provider benchmark and provisional choices
remain with Epic B; no uncertain dependency or weight is promoted here. Final
delivery still requires the outcome PR's CI/review and issue reconciliation.
