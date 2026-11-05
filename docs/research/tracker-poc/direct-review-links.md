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
The shared field has the same source-neutral shape for every film; detailed
identity evidence remains in the private research manifests. Do not infer
watched or unwatched status from a shared field.

Both importers preview by default and update only an empty dedicated field.
They do not replace an existing field even if a later batch contains additional
links; reconcile those manually before a future update. They recheck identity
and title before writing, but neither tracker provides compare-and-swap for
this operation. Run a single importer with no concurrent field editing, and
inspect the records before retrying an uncertain failure.

With the local POC services and credentials configured, run fictional checks:

```sh
uv run python docs/research/tracker-poc/direct_review_links_check.py
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
