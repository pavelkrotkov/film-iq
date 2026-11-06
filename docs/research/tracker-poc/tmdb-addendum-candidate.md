# Optional two-film TMDb addendum

This candidate is inactive by default. Do not create an approval artifact or
enable it until the user has approved the exact private preview. Approval of
the original 130 IDs does not approve these two IDs.

After approval, the operator may put an owner-only JSON artifact named
`tmdb-addendum-approval.json` in the existing project-private directory. Its
schema is below; the IDs and SHA-256 must come from the actual approved preview,
not this fictional example. `expires_at` must not exceed the earlier applicable
policy deadline; the implementation limits it to December 6, 2026 00:00 UTC.

```json
{
  "version": 1,
  "scope": "on-demand",
  "allowed_ids": [201, 202],
  "preview_sha256": "SHA-256 of the exact approved preview bytes",
  "expires_at": "2026-12-06T00:00:00Z"
}
```

Both bridges preserve their current behavior unless explicitly configured with
`FILMIQ_TMDB_ADDENDUM_DIR`. That directory must contain the addendum, the exact
addendum preview, `film-input.json`, and `tmdb-watched-lookup-preview.md`. For
each request the bridge reloads and verifies the original 130 approval and its
source hashes, the two additional IDs, preview digest and expiry. If the
addendum is missing, invalid or expired, only the original allowlist is used.
The combined allowlist is never written out. The original approval itself
continues to load as before when the addendum is absent.

For Kaneo, set `FILMIQ_TMDB_ADDENDUM_DIR` to the absolute project-private
directory when explicitly launching its bridge for an approved on-demand run.
For YouTrack, use the optional `youtrack-tmdb-live-bridge/compose.addendum.yaml`
in addition to the existing compose files and provide absolute file paths in
`FILMIQ_ADDENDUM_MANIFEST`, `FILMIQ_ADDENDUM_WATCHED_PREVIEW`,
`FILMIQ_ADDENDUM_APPROVAL`, and `FILMIQ_ADDENDUM_PREVIEW`. Its read-only file
mounts can continue to reference old inodes after replacement: recreate the
bridge to refresh or revoke mounted files. Do not enable this overlay now.

These settings do **not** technically distinguish an interactive request from
a scheduled one. The operator must run only explicit on-demand requests, keep
unattended watched-ID schedules disabled, stop the opt-in bridge afterward, and
follow existing cache, seven-day TTL, attribution, pacing and error rules.
The two bridge limiters are independent; keep the other bridge paused and stop
on 401, 403 or 429. The existing batch runner validates exactly 130 IDs and
must not be used to refresh these additional films. No cache deadline is
extended and no source payload belongs in tracker history.

Run the offline checks from the worktree root:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=docs/research/tracker-poc/youtrack-tmdb-live-bridge:docs/research/tracker-poc:src \
.venv/bin/python docs/research/tracker-poc/tmdb_addendum_candidate_check.py
```
