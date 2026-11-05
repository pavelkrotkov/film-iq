# MDBList read-through experiment

`mdblist_live.py` exposes an opt-in `GET /ratings/<tmdb-id>` on
`127.0.0.1:15177` for the local Kaneo UI origin `http://localhost:15174`.
It validates the current Kaneo session, reads the key from the ignored
`.cache/tracker-poc/private/mdblist-key`, and calls the documented
`GET /{media_provider}/{media_type}/{media_id}/` route using a server-side API
key. It does not store responses, log request paths, follow redirects, or write
to either tracker. Responses have `Cache-Control: no-store`. The API key is
sent to MDBList in the query string as described in its
[authentication documentation](https://api.mdblist.com/docs/authentication/);
it is not returned to the browser. The POC is designed for local use and has
not been hardened or validated for deployment on another host.

```sh
uv run python docs/research/tracker-poc/mdblist_live_check.py
uv run python docs/research/tracker-poc/mdblist_live.py
```

The UI should request data only after an explicit user action. Treat missing
or failed responses as unknown, show each value as *reported by MDBList*, keep
critic and audience scores distinct, and use only the source-provided URL when
the adapter returns one. MDBList's composite score is not an independent critic
score. Do not invent source pages for missing URLs. The adapter requires an
explicit integer `tmdbid` or `tmdb_id` matching the requested work; the schema
for the real response is not yet verified. The supplied allowlist uses the
reported rating-source code and validates provider URL hosts; classification
still needs confirmation against live responses.

The [published API docs](https://api.mdblist.com/docs/) state that the free tier
has 1,000 requests per account per day, with a 1,000-read limit per five
minutes. Limits are shared across the account's keys and applications; a 429
must not be retried in a loop. There is no cache here, so repeated clicks make
new requests. The [published service terms](https://mdblist.com/static/legal.html)
require compliance with third-party terms but do not establish the applicable
attribution or retention rights for the upstream ratings. Do not persist their
payloads or display them outside this opt-in experiment until those rights and
the account's actual plan have been assessed.

On 2026-11-05 the initial public-example lookup returned HTTP 403. One separate
sanitized-header diagnostic also returned 403, with a Cloudflare server/ray
header, no Cloudflare mitigation header and no rate-limit headers. This does not
establish whether the service, account/key, or edge blocked the request. No
provider response body or API key was printed or retained. The synthetic
adapter checks pass, but no live result, schema, entitlement, or account quota
has been verified.

A separate unauthenticated request to the public schema endpoint also returned
403 from this environment. The application code matches the documented route
and key format, but this observation does not identify the source of the denial.
