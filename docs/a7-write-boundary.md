# A7 write boundary evidence

`sync_one` previews one identified recommendation by default. Execution requires
both `execute=True` and explicit approval; it reads the movie and watchlist via
an injected backend, adds the movie if absent, then adds the watchlist entry if
absent. Failed reads propagate. The tests use only an in-memory stub; no network
client or live write is provided. The backend must distinguish confirmed absence
from failed or incomplete reads, map TMDB and Movary IDs correctly, and support
authoritative reads after uncertain writes. Sequential retries are exercised;
concurrent writers and eventual consistency are not established by these tests.

The installed instance's version and OpenAPI contract were not available for
inspection. Before implementing an HTTP adapter, verify its movie lookup and
TMDB addition and watchlist lookup and addition methods, paths, authentication,
request and response schemas, pagination/completeness, duplicate behavior, and
read-after-write behavior, including a lost response. The published
[API site](https://api.movary.org/) did not expose a readable contract to this
inspection. Do not infer a write endpoint from the separate A2 read client.

Gate A remains open: A1–A6 are not integrated, the source-to-offer path is
synthetic, and the approved Movary round trip and its measurements are absent.
Any live watchlist change requires a separate explicit user authorization.
