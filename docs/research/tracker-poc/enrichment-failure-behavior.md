# Fictional worker: film metadata and provider failures

The backend-neutral fixture worker obtains film metadata and availability
separately. If the film metadata succeeds but the provider lookup raises an
exception, the worker now ensures the film record exists without replacing
availability. It raises `AvailabilityRefreshError` with the confirmed tracker
record ID; the original exception is available as `source_error` for callers
that classify rate limits or authorization failures. Its message and normal
traceback do not print the provider exception, which could contain a credential
or URL. A backend failure or missing record ID is not reported as a confirmed
save. Missing or partial provider responses still do not replace availability.

Run the fictional checks from the worktree root:

```sh
uv run python docs/research/tracker-poc/enrichment_independent_failure_check.py
uv run python docs/research/tracker-poc/youtrack_enrich_fixture_check.py
```

The check exercises both adapter classes with in-memory tracker transports:
provider failure on first import, metadata persistence, a later user synopsis
and genre edit, a duplicate-free successful retry, unchanged preferences and
preservation of an existing availability observation on another failure.
It also checks timestamp validation and unconfirmed backend responses. This is
the synthetic fixture worker, not a change to the live TMDb bridges; no real
tracker, film, provider or browser session was used. Sequential retries are
covered; concurrent imports remain outside the POC's demonstrated guarantees.
