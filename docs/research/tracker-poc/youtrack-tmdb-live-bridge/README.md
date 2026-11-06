# Candidate YouTrack TMDB read-through bridge

This separate app and service are installed, configured and attached to the
synthetic and real film projects. The existing synthetic fixture remains a
separate app and port. An authorized live runtime check is recorded below;
main-menu browser invocation and image-cache behavior remain unverified.

The issue-scoped handler checks the signed-in YouTrack user, project and issue
visibility and obtains the TMDB ID from the issue field, not from the request
body. It calls only `127.0.0.1:15178`, authenticated with a YouTrack secret
setting. The Python bridge requires explicit live enablement, a server-only
bridge token and TMDB credential at startup. Before each requested film read,
it reloads and validates a positive allowlist; missing, malformed, empty,
duplicate or unsupported-destination configuration fails closed. One film read
may make several upstream calls, and the allowlist is not rechecked between
them. A denied ID never reaches the provider. The bridge validates the returned ID, limits poster
images to the approved image host, propagates HTTP 429, and uses the same
`tmdb_readonly.read_movie` and response serializer as the Kaneo POC. JSON
responses carry `Cache-Control: no-store` at both layers. The service has no
response persistence, and its request logger is disabled.

The optional `FILMIQ_TMDB_PACE=1` setting serializes this bridge's upstream
attempts and starts them at least one second apart, including attempts that
fail. It is off by default; values other than `0` or `1` fail startup. The
Kaneo bridge accepts the same setting, but the two processes do not coordinate
their limiters, nor do they control other clients using the same credential.
For a bounded batch, run the two passes sequentially and avoid other live
refreshes. TMDB 401/403 errors, including those from optional poster
configuration or provider requests, now stop the read and surface as a generic
502; 429 still surfaces as 429. No automatic retry is made and the bridge does
not expose `Retry-After`.

For the approved collection run, pause live refresh on the idle bridge with
`FILMIQ_TMDB_REFRESH_ENABLED=0`; its authenticated cache and catalog reads
remain available. Start with YouTrack paused and Kaneo active, then pause Kaneo
before enabling YouTrack. Both bridges must use `FILMIQ_TMDB_PACE=1`; the
batch preflight checks their authenticated effective settings. Live refresh is
temporarily unavailable in the paused UI. Other clients using the credential
must remain idle. Do not edit the approval file during the run: the bridges
reload it and do not pin its bytes.

From the worktree root, immediately before recreating the YouTrack bridge for
the collection, validate the original approval and its source artifacts. This
command stops on validation failure and preserves both catalog and cache mounts;
set `refresh=0` for the first pass and `refresh=1` only after Kaneo is paused:

```sh
refresh=0
PYTHONPATH=docs/research/tracker-poc/youtrack-tmdb-live-bridge:docs/research/tracker-poc:src \
  .venv/bin/python -c 'from pathlib import Path; from live_bridge import validate_collection_approval; p = Path(".cache/tracker-poc/private"); validate_collection_approval((p / "tmdb-approval/approved-ids.json").read_bytes(), (p / "film-input.json").read_bytes(), (p / "tmdb-watched-lookup-preview.md").read_bytes()); print("Collection approval validated")' && \
FILMIQ_APPROVAL_DIR="$PWD/.cache/tracker-poc/private/tmdb-approval" \
FILMIQ_CATALOG_APPROVAL_HOST_DIR="$PWD/.cache/tracker-poc/private/tmdb-approval" \
FILMIQ_YOUTRACK_CACHE_DIR="$PWD/.cache/tracker-poc/private/tmdb-live-cache/youtrack" \
FILMIQ_REVIEWED_CATALOG_FILE="$(cd ../.. && pwd)/.cache/epic-c/results/reviewed-display-catalog-expanded-20261031.json" \
FILMIQ_BRIDGE_UID="$(id -u)" FILMIQ_BRIDGE_GID="$(id -g)" \
FILMIQ_TMDB_BRIDGE_ENABLE_LIVE=1 FILMIQ_TMDB_PACE=1 FILMIQ_TMDB_REFRESH_ENABLED="$refresh" \
docker compose -f docs/research/tracker-poc/compose.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.live.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.catalog.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.cache.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.catalog-approval.yaml \
  --profile tmdb-live-bridge up -d --no-deps --force-recreate --pull never tmdb-live-bridge
```

An optional issue-scoped catalog endpoint reads existing reviewed facts from a
configured local file without a TMDB request or tracker write. It checks issue
visibility, the issue's ID and current title, the approved-ID list, and the
catalog's freshness and title match. It returns only limited, attributed facts;
missing, expired, or mismatched data is unknown. It does not verify identity or
provide a synopsis, poster, or availability. The optional
`compose.catalog.yaml` mounts the catalog and adapter read-only; set
`FILMIQ_REVIEWED_CATALOG_FILE` to the existing catalog file before applying it.
By default catalog reads use the same allowlist as live provider/cache requests.
The optional `compose.catalog-approval.yaml` instead mounts a dedicated catalog
approval directory read-only and sets `FILMIQ_CATALOG_APPROVAL_DIR`. This uses
the same `approved-ids.json` schema, but is checked only for local catalog
reads; provider and cache routes continue to use their own allowlist. Each is
reloaded on every applicable request. A missing or malformed separate catalog
approval fails closed; it never falls back to the provider allowlist. This
override can preserve existing approved local catalog visibility during a
narrower live pilot without broadening what may be sent to TMDB.
The file mount can retain an older inode after atomic replacement, so stop or
recreate the bridge when replacing or revoking the source. This does not purge
the existing catalog or backup copies.

For the current worktree, the optional mount can be applied with the following
command after the existing bridge credentials and approval directory are in
place. It recreates only the bridge container and interrupts active requests:

```sh
catalog_file="$(cd ../.. && pwd)/.cache/epic-c/results/reviewed-display-catalog-expanded-20261031.json"
if [ -f "$catalog_file" ]; then
FILMIQ_APPROVAL_DIR="$PWD/.cache/tracker-poc/private/tmdb-approval" \
FILMIQ_BRIDGE_UID="$(id -u)" FILMIQ_BRIDGE_GID="$(id -g)" \
FILMIQ_TMDB_BRIDGE_ENABLE_LIVE=1 FILMIQ_REVIEWED_CATALOG_FILE="$catalog_file" \
docker compose -f docs/research/tracker-poc/compose.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.live.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.catalog.yaml \
  --profile tmdb-live-bridge up -d --no-deps --force-recreate --pull never tmdb-live-bridge
else
  printf 'Reviewed catalog not found\n' >&2
fi
```

The allowlist is a JSON object with `version: 1`, a nonempty unique list of
positive integers in `allowed_ids`, and exactly `api.themoviedb.org` and
`image.tmdb.org` in `destinations`. Optional nonempty audit strings are
`watched_approval_preview_sha256` and `source_manifest_sha256`. The allowlist
is an authorization artifact: the operator must ensure it contains only IDs
approved for those destinations and refresh/revoke it when approval changes.
The code does not infer authorization from a film's lifecycle or watched state.

## Checks and package

From the worktree root, these checks use only synthetic values and an injected
fake reader; they make no network calls:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/youtrack-tmdb-live-bridge/live_bridge_check.py
node docs/research/tracker-poc/youtrack-tmdb-live-bridge/metadata_check.cjs
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/tmdb_live_check.py
docker compose -f docs/research/tracker-poc/compose.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.live.yaml \
  config --no-env-resolution --no-interpolate --quiet
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/research/tracker-poc/youtrack-tmdb-live-bridge/build_package.py
```

The builder writes a separate app archive to
`.cache/tracker-poc/youtrack-tmdb-live-isolated.zip` and prints its SHA-256.
The builder does not install the app. Do not replace the separate fixture app.

## Reproducing the live setup

The following steps describe setup in another authorized environment; the
local service and app are already configured and running.

1. Confirm the approved ID list and exact destinations out of band. Place the
   exact allowlist as `approved-ids.json` in a dedicated, ignored,
   owner-controlled project directory containing no other private files. Set
   `FILMIQ_APPROVAL_DIR` to that directory's absolute path, and set
   `FILMIQ_BRIDGE_UID` and `FILMIQ_BRIDGE_GID` to a non-root container identity
   that can read the directory and file. A directory mount permits an atomically
   replaced file to be re-read; a bind mount of the individual file could retain
   an older inode. Verify replacement/revocation behavior and Docker Desktop's
   mount ownership before use. A missing or unreadable file prevents startup.
2. Privately provision `.cache/tracker-poc/private/youtrack-tmdb-live.env`
   with `FILMIQ_BRIDGE_TOKEN` (at least 32 ASCII non-whitespace characters)
   and either `TMDB_READ_ACCESS_TOKEN` or `TMDB_API_KEY`. Keep it out of Git,
   shell history and logs. A read access token avoids placing an API key in an
   upstream URL query. Environment variables remain visible to administrators
   who can inspect the container; protect Docker access accordingly.
3. Verify the pinned Python image and architecture locally before use. The
   current Compose image is pinned to SHA-256 digest
   `f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c`.
   The Compose override has no
   published port, shares the YouTrack network namespace and exposes the
   bridge only on its loopback. Sharing a namespace allows the bridge to reach
   YouTrack's loopback services and is not a production isolation boundary.
4. Install the separate candidate app only after reviewing its exact archive;
   attach it to the intended project, configure its secret `bridgeToken` to
   the same value as `FILMIQ_BRIDGE_TOKEN`, and verify requirements. Confirm
   that port 15178 is free inside the YouTrack namespace. The app and service
   remain distinct from the synthetic fixture at port 15176.
5. Only after the exact allowlist and destination authorization are confirmed,
   set `FILMIQ_TMDB_BRIDGE_ENABLE_LIVE=1` and start only `tmdb-live-bridge`
   with `--no-deps --no-recreate --pull never`. Without that explicit setting,
   startup fails. Use an explicit user action for each approved film; stop on
   429. Confirm authenticated and unauthorized responses, issue visibility,
   `no-store` headers and non-disclosure of credentials with synthetic cases
   first. Do not submit an unapproved real film ID to the provider.

With `FILMIQ_APPROVAL_DIR`, `FILMIQ_BRIDGE_UID` and `FILMIQ_BRIDGE_GID` already
set, the later start command is:

```sh
FILMIQ_TMDB_BRIDGE_ENABLE_LIVE=1 docker compose \
  -f docs/research/tracker-poc/compose.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-live-bridge/compose.live.yaml \
  --profile tmdb-live-bridge up -d --no-deps --no-recreate --pull never tmdb-live-bridge
```

This reproduction command is not part of the synthetic checks above.

## Observed runtime check

The separate live service and app are running, configured and attached to
`FILMPOC` and `FILMREAL`. An anonymous request returned 401, and an unapproved
synthetic identifier returned 403. One user-approved watched-film lookup
returned HTTP 200 with `no-store`, a poster path and a complete provider
response. Later non-retaining checks through each backend processed all 130
authorized IDs: each returned 130 poster paths and 109 complete US provider
responses; 21 provider results were unknown. Those responses do not establish
the user's entitlement or independently verify viewing history. No film
identifiers, titles or provider links are recorded here.

The YouTrack issue-scoped endpoint is under
`/api/issues/<issueId>/extensionEndpoints/<app>/<handler>/<endpoint>`.
The full-page main-menu widget has no inherent issue context: using
`host.fetchYouTrack` with that issue path may work, but main-menu invocation,
its required permissions and response behavior are unverified. Browser poster
loading may retain images or disclose a referrer independently of the JSON
`no-store` header; no poster retention or browser image behavior has been
verified. Keep the existing TMDB logo, disclaimer and JustWatch credit when
displaying results. The local endpoint's no-store header does not establish
provider accuracy, viewing entitlement, licensing clearance, or the absence of
logs in YouTrack, Docker, the browser, a proxy or the network.
