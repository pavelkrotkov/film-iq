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
