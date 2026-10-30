# A7 live validation — 2026-10-30

The saved Movary token was loaded from the selected project's ignored, mode-0600
`.env`. No credential value was printed, committed or copied into this report.
Browser automation was not used for these integration checks.

| Check | Observed result |
| --- | --- |
| `GET /api/v1/authentication/token` | HTTP 200 |
| Implemented paginated played reader | Complete, 0 records |
| Implemented paginated history reader | Complete, 0 records |
| Implemented paginated watchlist reader | Complete, 0 records |
| Supported ratings CLI export, previous run | Valid header-only CSV, 0 ratings |
| Implemented movie-search read for the candidate | HTTP 500, reproduced with a direct authenticated GET |

The installed application log reports `TMDB API key is probably not set or
invalid.` Its `TmdbClient.php` maps an upstream HTTP 401 to that exception.
This distinguishes a TMDB authorization failure from a Movary-token failure or
network timeout. Raw application logs and credential-bearing requests were not
retained. The user subsequently supplied a valid TMDB v3 key: direct TMDB
authentication, film details/credits and US watch-provider requests succeeded.
The configured Movary search is still unverified after correction: automatic
approval review rejected transferring the key to Hermes and recreating the
service without explicit authorization. No remote configuration was changed.

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

## Exact pending approvals

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

Gate A remains open until the approved configuration/search and selected-write
round trip pass. No movie/watchlist POST was attempted. An empty
personal account cannot demonstrate a live rated-only example; deterministic
fixtures cover that case. No personal rating or watchlist was changed.
