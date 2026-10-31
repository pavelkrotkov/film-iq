# Offline-prepared candidate fetch path

The `tmdb` and `motn` candidates are **not selected or enabled production feeds**.
No scheduler is installed. Existing B4 observation code/configuration is unchanged;
the genuine third date and reviewed B8 intended-use/provider decision still govern
activation. This path is tested with synthetic injected responses only.

Preview a reviewed work manifest without opening a database, reading credentials,
requesting a provider or persisting observations:

```sh
uv run python -m film_iq.availability.candidate_command --provider tmdb --input .cache/reviewed-works.json --max-requests 2
```

Provider choice is mandatory (`tmdb` or `motn`), with no default winner. Input is
an array of objects containing positive `tmdb_id`, IMDb `imdb_id`, nonblank
`reviewer`/`evidence` and explicit boolean `independent: true`. These attest an
already independent work crosswalk, not an automatically accepted provider hit
or exact cut. The entire batch validates before requests, including duplicate
IDs and an explicit nonnegative finite integer request cap. Oversized batches
are rejected, never silently truncated.

Only a future explicitly authorized `--live` invocation can call the network.
It also requires an existing `--database` with that exact provider source's
registered, currently allowed finite `CachePolicy`. This command never registers
or grants a policy or creates a database in dry-run mode. Header-only credentials
are `TMDB_READ_ACCESS_TOKEN` and `MOVIE_OF_THE_NIGHT_API_KEY`; no key enters a URL,
report or exception. Requests have a 30-second timeout, no redirects or retries.
401/403/429 or explicit zero supported remaining-quota headers stop the run;
unrequested work is labelled skipped, not absence. There is no rolling-quota
scheduler or claim that unknown account allowance is unlimited.

TMDB reuses the existing pure normalizer and validates the exact reviewed integer
work ID. Native requires exact `movie/TMDB-ID`, IMDb ID and `showType: movie`.
Missing/invalid US data, HTTP/decode/transport failures remain unknown. Explicit
valid empty US containers can be complete; invalid rows make a partial response
while preserving valid positive variants. No mapper invents `plan_scope`, plan,
cut, price or personal entitlement; unknown-plan observations cannot advance a
comparison baseline or generate removal events. The existing guarded ledger and
discovery reader preserve source/time/quality/add-on/currency variants and rights.

Native price strings convert exactly with `Decimal` and integer ratios, never
float rounding. The bounded supported ISO4217 minor-unit set is USD/EUR/GBP/CAD/
AUD=2, JPY=0, KWD=3, verified against [SIX List One](https://www.six-group.com/en/products-services/financial-information/market-reference-data/data-standards.html).
Unsupported currencies, fractional minor units, booleans, nonfinite or negative
amounts reject that row as partial rather than guessing.

The native [OpenAPI](https://github.com/movieofthenight/streaming-availability-api/blob/main/openapi.yaml)
defines `availableSince` as detection time and `expiresOn` as last day to watch.
Their exact integer Unix seconds are preserved as `provider_detected_at` and
`provider_last_day_at` in UTC, **not** effective addition or exact expiry instants.
The existing `asserted_added_on`/`asserted_expires_at` remain unknown. New nullable
fields are omitted from legacy canonical encoding when absent, preserving old
observation hashes/replay. Visible credits use the named providers' required
public credit/link and TMDB logo/notice; operator notes grant no license or
compliance exemption. JSON and text use still require the reviewed intended-use
and retention basis; no blanket exemption is asserted.
