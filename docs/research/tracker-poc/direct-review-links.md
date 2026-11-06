# Direct review links in the tracker POCs

The POCs keep direct critic-review and aggregator title-page links in fields
separate from the accepted discovery evidence. Research manifests are private,
project-local and ignored by Git. They contain source-page identity checks and
corroboration; no review prose or ratings are copied. A reviewed source match
does not by itself independently verify a supplied TMDB identity or a personal
viewing. Source-page terms still apply, and a link can become stale.

`direct_review_links.py` validates all supplied batches before a write. It
requires a matching source identity and title/director evidence, retains
uncertainty, and holds conflicting identities out across every supplied batch.
Each `checked_at` may be a calendar date when that is the only recorded
precision, or a timestamp with an explicit timezone; the date-only form does
not assert a particular time of day.
The shared field has the same source-neutral shape for every film; detailed
identity evidence remains in the private research manifests. Do not infer
watched or unwatched status from a shared field.

Both importers preview by default and fill only untouched dedicated fields.
Kaneo preserves every existing value row, including an empty one; its pinned
implementation writes an empty row on clear. YouTrack checks custom-field
activity before filling a null field and preserves it if the review field has
changed. Unreadable history stops the import. The YouTrack history safeguard is
covered by fictional offline checks. A local FILMPOC test assigned and cleared
the text field on one fictional issue, then found the changes using the same
guard across multiple one-item activity pages. The full import test initially
stopped because two existing fictional issues shared a reserved fixture ID.
After checking their roles, a single old runtime-test issue was given an unused
fictional ID; the documented cache UI fixture was unchanged, and its isolated
endpoint still returned the expected fictional metadata and subscription.
The old and new IDs and readback evidence are retained privately. A subsequent
full live test passed initial import, repeat, clear, paginated history and
reimport without replacing the clear, while preserving the fictional synopsis
and source evidence. Both newly created test issues were retained. The full
test now checks for invalid or duplicate IDs before creating a fixture.

Replacing a field definition or incomplete tracker history may lose the
distinction between an untouched and cleared field. The separate direct history
check was later changed to create and retain a uniquely marked fictional issue
on each run instead of selecting the latest issue; that revised procedure has
not been rerun live. Existing fields are not augmented when a later batch
contains additional links; reconcile those manually. Both importers recheck
identity and title, but neither provides compare-and-swap. Run one importer
with no concurrent field editing, and inspect records before retrying an
uncertain failure.

With the local POC services and credentials configured, run fictional checks:

```sh
uv run python docs/research/tracker-poc/direct_review_links_check.py
uv run python docs/research/tracker-poc/kaneo_direct_reviews_clear_check.py
uv run python docs/research/tracker-poc/youtrack_review_import_check.py
uv run python docs/research/tracker-poc/kaneo_direct_reviews_live_check.py --directory .cache/tracker-poc
uv run python docs/research/tracker-poc/youtrack_review_live_check.py
node docs/research/tracker-poc/ui/direct_reviews_check.mjs
```

The live checks create and retain fictional test records. For a private
preview, pass the ignored source manifest and every reviewed batch in a single
invocation. Kaneo uses repeated `--input` flags plus `--project` and
`--cookie-file`; YouTrack uses repeated `--manifest` flags plus `--project
FILMREAL`. Add `--apply` only after reviewing the counts. See each script's
`--help` for the complete arguments. Do not run a subset of related batches:
the holdback check only considers the manifests supplied in the invocation.

The Kaneo importer also accepts `--api-key-env` instead of `--cookie-file`.
This reads an independently provisioned `KANEO_API_KEY` from the environment,
sends it as a bearer header only to the configured loopback instance, and
refuses redirects; do not put the key in the command line, logs or Git. Use
the exact same complete set of input batches, preview first, and add `--apply`
only when the preview is correct. Stop on 401, 403, 429 or uncertain write
outcomes; inspect before retrying. No existing browser session or cookie is
needed by this mode.

The pinned v2.49.0 source checks project-read and task-read permissions for
the importer's reads and task-update for setting an existing value; creating
a missing field additionally requires project-update. API key restrictions
intersect with the owner's workspace permissions. The v2.49.0 key-creation
dialog exposes name and expiry but no scope selector, so a UI-created key's
access should not be described as narrowly scoped. The documented API key
mode has only been exercised with fictional in-process transport, not a live
key or real tracker. The mode does not itself provision a credential or
authorize access to one.

On 2026-11-05, eight batches identified 50 eligible films with 78 links and one
held-back identity. Both local POC imports filled empty fields, and readback
matched all links. A repeat made zero writes. The Kaneo film view can display
these links, and the YouTrack field is attached for the native issue view. A
newer embedded app with a direct-links view showed text-labeled cards but their
controls remained disabled during the browser observation. A subsequent
navigation fix was followed by isolated Brave walkthroughs in both POCs. Each
showed a fictional individual-review link and a fictional aggregator link with
the expected distinct labels; the links were not opened. Both custom views hide
links when the current title differs from the reviewed source title, pending
revalidation. Real-film link rendering has not been checked in the browser.

On 2026-11-06, a previously researched critic-review page and revisioned source
evidence supported one additional link. The retained evidence recorded the
check day but not a time, so the imported value preserves date-only precision.
All eight earlier batches plus the new batch validated together: 51 eligible
films and the same one held-back identity. A single YouTrack write filled the
new film's empty, previously unedited review field; readback confirmed the link.
The other 129 issue projections, the target's other projected fields, the full
watched property and preferences matched before and after. The source's film
identity is not independently verified. Kaneo has not received this additional
link; a separate candidate aggregator page remains unimported because its
director comparison is unresolved. No new external requests or Movary writes
were made during this import. The operation assumes no concurrent writer.

Both deployed film interfaces can also show director names already recorded in
the direct-review identity evidence, and search those names without fetching
new data or changing tracker fields. They retain all reported names and label
them as review identity evidence whose film identity has not been independently verified;
the names are not promoted to canonical directors. The existing matching-ID and
matching-title guards apply to both search and display. A local read of 130
YouTrack film issues counted 50 with matching-ID and matching-title review
evidence, including 13 whose separate source-director field was empty. This
aggregate read was not a browser rendering check or independent identity
verification. Fictional tests exercised the two filters, display labels,
conflicting names, malformed or missing data, and changed title or ID.
The deployed YouTrack package and Kaneo bundle matched the reviewed builds;
the checked watched property, preferences, settings, usages and attachment
metadata were unchanged. No real-film browser walkthrough was performed for
this change. A 1,000-film fictional review-evidence search measured 3.18 ms
median / 3.65 ms p95 for Kaneo's extracted filter and 3.48 ms / 3.70 ms for
YouTrack's, in 50 warmed Node samples. These are CPU-only measurements; they
exclude browser rendering, network and data loading.
