# A7 write boundary evidence

`uv run film-iq sync --title "Selected film" --tmdb-id 123` previews without
credentials or network access. After reviewing that exact selection, an operator
can explicitly pass both `--execute --approve`; execution reads `MOVARY_URL`,
`MOVARY_USERNAME` and `MOVARY_TOKEN` from local environment configuration. Do not
put credentials into command arguments, report inputs or Git. The CLI does not
automatically load `.env`; load your trusted project-local configuration for an
already approved execution, for example:

```sh
set -a
. /path/to/project/.env
set +a
```

The [approved live POC](a7-live-validation.md) validates one selected round trip.
This guide is not authorization for future personal-state changes.

`sync_one` previews one identified recommendation by default. Execution requires
both `execute=True` and explicit approval; it reads the movie via an injected
backend, adds the movie if absent, then reads the watchlist and adds the entry
if absent. A watchlist read failure can therefore follow a movie addition, but
prevents a watchlist addition. Failed reads propagate. The 0.82.1 backend accepts an injected HTTP
transport, with authentication and response decoding supplied by its caller;
credential-free tests use stubs, while the linked live trace exercises the CLI
and real transport. Invoke it through
`sync_one`; direct backend writes also require explicit `approved=True`, and
watchlist additions must match the ID confirmed by its selected movie lookup or
addition. A failed lookup clears the previously confirmed ID.

The [pinned 0.82.1 OpenAPI contract](https://github.com/leepeuker/movary/blob/0.82.1/docs/openapi.json)
documents the search, addition and paginated watchlist routes used here. Search
is remote and title based: only an exact TMDB result with an explicit null
Movary ID establishes absence; a missing result stops the sync. Pagination must
be complete and consistent. Search permits empty advertised trailing pages only
when preceding 20-result TMDB pages, a short final result page, and the pinned
Movary pagination calculation explain it. All requests must succeed and an
exact identity remains required.
Retrying after a lost response re-reads state; the
stub tests this. The installed 0.82.1 live POC verifies immediate readback and a
same-selection CLI retry with zero further POSTs and no duplicate. Lost-response
recovery and concurrent changes remain unverified live. The CLI supplies a stdlib
HTTP transport; credentials are read only for explicitly approved execution.

Gate A's narrow real source-to-offer-to-approved-watchlist trace is documented in
the live validation, including installed version, empty ratings export, measured
request order and limitations. Nonempty rated-only behavior remains fixture-backed.
Any live watchlist change requires a separate explicit user authorization.
