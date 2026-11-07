# Synthetic YouTrack metadata bridge experiment

This isolated experiment is installed as a separate app from the film browser. It accepts only
two hardcoded fictional IDs in `FILMPOC`, calls `read_movie` with a deterministic
fixture provider, and has no code path to live TMDB. The approved list in both
the handler and bridge is positive and synthetic; the existing watched-film
research approval does not authorize sending other IDs to TMDB. The separate
live integration uses its own authorization gate and exact destination scope.

The issue-scoped handler checks the caller and issue visibility, reads the ID
from the issue field, and sends it to the fixture bridge using YouTrack's
documented secret settings and HTTP connection API.
The Python bridge requires a bearer token, uses no persistent response store,
and returns `no-store` responses. The handler also sets `no-store` and preserves
a synthetic 429. The fixture does not serve real poster images or prove browser
image-cache behavior.

Run from the worktree root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=docs/research/tracker-poc:src \
  .venv/bin/python docs/research/tracker-poc/youtrack-tmdb-bridge-poc/fixture_check.py
```

The check starts a short-lived loopback-only WSGI server, then runs the handler
in a Node VM with a fake implementation of YouTrack's HTTP API. It verifies
guest and visibility denial, project and ID restrictions, bearer authentication,
a successful fictional read and 429 propagation. The HTTP calls stay on
loopback; the provider never contacts TMDB. The check needs permission to bind a
local socket and suppresses request logs.

The Node VM test alone does not establish pinned YouTrack runtime behavior.
The separate runtime check below verified the issue-scoped handler, setting
handoff, shared-namespace route and response headers for an administrator.
Main-menu browser invocation, signed-in restricted-user visibility and image
cache behavior remain unverified. YouTrack in Docker cannot reach a host-only
service via its own loopback interface.

## Prepared container and separate app package

`compose.fixture.yaml` adds an opt-in service that shares the existing
YouTrack container's network namespace. It binds only to `127.0.0.1:15176`
inside that namespace, publishes no ports, mounts only code read-only, and
uses an unprivileged user. Sharing the namespace also lets the fixture reach
YouTrack's other loopback services; this is not a production isolation model.
The bridge uses a fixture-only test value, not a production credential. The
service is hardwired to the fixture provider and the two
fictional IDs; it cannot fetch TMDB or accept live film IDs.

The fixture Python image is pinned to SHA-256 digest
`f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c`.
The fixture service ran in the local YouTrack network namespace with no
published fixture port and was stopped after the test. Image contents and
production isolation have not been audited.

The isolated app has the distinct name `filmiq-tmdb-fixture-isolated`. Build
its archive and validate the Compose model without reading service env files:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/research/tracker-poc/youtrack-tmdb-bridge-poc/build_fixture_package.py
docker compose -f docs/research/tracker-poc/compose.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-bridge-poc/compose.fixture.yaml \
  config --no-env-resolution --no-interpolate --quiet
```

The prepared archive is `.cache/tracker-poc/youtrack-tmdb-fixture-isolated.zip`.
Its SHA-256 at preparation was
`311db8e3173e6deded03bbfc8b32b2ca9790bd753d1cfced1ec793055efc61f4`;
rebuilding prints the checksum again. It contains only `manifest.json`,
`settings.json`, and `metadata.js`. The separate fixture app is installed,
configured and attached to `FILMPOC`.

To reproduce the setup in a separate authorized environment, first verify YouTrack is already running,
the fixture port is free inside its network namespace, the image is locally
available and pinned, and the app name does not collide. Start only the fixture
without dependencies or recreation:

```sh
docker compose -f docs/research/tracker-poc/compose.yaml \
  -f docs/research/tracker-poc/youtrack-tmdb-bridge-poc/compose.fixture.yaml \
  --profile tmdb-fixture up -d --no-deps --no-recreate --pull never tmdb-fixture
```

Verify no fixture port is published. Install the **separate** archive only in
the test instance, configure its loopback address and the fixture-only value
defined by the server, and attach it only to `FILMPOC`. Using newly created
fictional issues, set `FilmIQ TMDB ID` to each fixture ID in `metadata.js` and
invoke the issue-scoped `metadata/read` endpoint as an authorized user. Check
success, 429, no-store, wrong-token denial, guest/unauthorized/other-project
denial, and rejection of a non-fixture ID. Confirm the bearer value does not
appear in responses or logs and no real provider request occurs. Afterwards,
stop only `tmdb-fixture`; removing the separate app or synthetic issues is a
separate state change to review under the project rules.

The reproduction steps above are instructions. The observed runtime evidence
and remaining limitations are recorded below.
For any later main-menu integration, do not assume `host.fetchApp(...,
{scope: true})` has an issue context: the main-menu widget is not hosted by a
specific issue. JetBrains documents the issue-scoped endpoint under
`/api/issues/<issueId>/extensionEndpoints/<app>/<handler>/<endpoint>`; calling
that relative path with `host.fetchYouTrack` may be a route from the menu widget,
but its permissions, confirmation behavior, and response handling have not
been tested for this endpoint in the pinned runtime.

## Observed synthetic runtime check

On 2026-11-05 the separate app was installed and its fixture service started
for an authorized synthetic test on YouTrack 2026.2.19728. Two new fictional
issues were left in place. Using the admin
account, the issue-scoped endpoint returned the expected fictional data with
HTTP 200 and `no-store`, and the other fixture returned HTTP 429 and `no-store`.
An anonymous request returned 401; a nonexistent issue returned 404; an
unapproved fixture ID returned 403. The modified synthetic ID was restored
and read back. These results exercise secret-setting handoff and the actual
YouTrack-to-fixture route. They do not establish signed-in restricted-user
visibility or main-menu widget invocation.

`runtime_check.py` creates **two new** synthetic issues each time it runs and
leaves them in place. If creation times out or returns an uncertain result,
inspect `FILMPOC` before retrying. Its local API checks use the existing admin
token without printing it; they never call live TMDB or inspect real films.
