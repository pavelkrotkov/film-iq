# A7 write boundary evidence

`sync_one` previews one identified recommendation by default. Execution requires
both `execute=True` and explicit approval; it reads the movie via an injected
backend, adds the movie if absent, then reads the watchlist and adds the entry
if absent. A watchlist read failure can therefore follow a movie addition, but
prevents a watchlist addition. Failed reads propagate. The 0.82.1 backend accepts an injected HTTP
transport, with authentication and response decoding supplied by its caller;
tests use only stubs and no live write was performed. Invoke it through
`sync_one`; direct backend writes also require explicit `approved=True`, and
watchlist additions must match the ID confirmed by its selected movie lookup or
addition. A failed lookup clears the previously confirmed ID.

The [pinned 0.82.1 OpenAPI contract](https://github.com/leepeuker/movary/blob/0.82.1/docs/openapi.json)
documents the search, addition and paginated watchlist routes used here. Search
is remote and title based: only an exact TMDB result with an explicit null
Movary ID establishes absence; a missing result stops the sync. Pagination must
be complete and consistent. Search permits an empty advertised last page only
when preceding 20-result TMDB pages, a short final result page, and the pinned
Movary pagination calculation explain it. All requests must succeed and an
exact identity remains required.
Retrying after a lost response re-reads state; the
stub tests this, but actual read-after-write consistency, duplicate behavior,
concurrent changes and the installed instance's version are not verified.
Confirm those properties on the target instance before use. No credentials or
HTTP transport implementation are configured by this module.

Gate A remains open: A1–A6 are not integrated, the source-to-offer path is
synthetic, and the approved Movary round trip and its measurements are absent.
Any live watchlist change requires a separate explicit user authorization.
