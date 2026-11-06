# Proposed TMDb source-use decision: one-film local pilot

**Status: proposed, not activated.** This is an engineering assessment for a
temporary proof of concept, not legal advice or certification. It neither
enables the cache nor selects a provider for the wider product.

## Intended use and proposed decision

For the private, self-hosted, noncommercial, deterministic POC, propose a
limited test of current TMDb movie metadata and US watch-provider observations
for **one TMDb ID already covered by the user's existing authorization**. The
pilot may display a poster for that film using the existing authorized image
scope. It will not send ratings, personal notes, watch dates, or watched-status
flags to TMDb. It has no public data API, commercial use, runtime chatbot or
model, or provider-data training, evaluation, or improvement use. AI-assisted
software development alone is not itself a published TMDb exception; treating
this particular deterministic runtime as non-model use is our interpretation.

Subject to the controls below and the remaining review, the proposed decision
is to permit this single-film pilot, without treating that decision as a grant
for additional IDs, redistribution, historical datasets, production use or
other third-party content. A working key and the user's authorization to make
requests do not independently establish the provider's data rights.

## Source evidence and attribution

- TMDb's [FAQ](https://developer.themoviedb.org/docs/faq) describes free
  noncommercial API use with attribution and specifies the TMDb logo and
  nonendorsement notice in an About or Credits section. The interface should
  show the approved, unmodified logo linked to TMDb and the specified notice.
- TMDb's [movie watch-provider documentation](https://developer.themoviedb.org/reference/movie-watch-providers)
  identifies JustWatch as the source and requires JustWatch attribution. Keep
  its visible credit and preserve the TMDb information link returned by the
  endpoint. The endpoint is not a full deep-link feed.
- The project's [October 31, 2026 source review](../availability/intended-use-20261031.md)
  recorded that the [canonical TMDb terms](https://www.themoviedb.org/api-terms-of-use)
  then displayed a six-month caching ceiling and a requirement to cease use and
  purge on termination. The web reader could not independently recheck that
  page on November 5; the earlier observation is dated evidence, not proof
  that the terms remain unchanged. The FAQ and endpoint documentation do not
  independently establish a retention period or permission for historical
  copies.

## Storage, expiry and operation

- Retain only the current normalized metadata and latest usable US availability
  observation in the dedicated, ignored project-local cache. Keep subscriptions
  separate from rentals and purchases. A failed or partial provider request is
  not evidence that a service is absent, and must not overwrite a previous
  complete availability observation with a negative result.
- Treat each metadata and availability observation as fresh for at most seven
  days, subject to earlier policy expiry or termination. Seven days is our
  conservative POC choice, not a claimed TMDb requirement. Copies or restores
  never renew an observation's original deadline. In all cases retain nothing
  beyond the earlier applicable source or policy deadline; the prior review's
  six-calendar-month ceiling is an outer limit, not permission to keep data
  that long or an assurance that any particular content can be cached.
- Do not place source payloads in tracker records or history, Movary, exports,
  reports, screenshots, Git, or project-created backups. Inventory actual
  generated cache files and any separately retained copies. Verify backup and
  sync exclusions and assess existing browser image caches before activation.
  Poster `no-store` and object-URL revocation reduce browser HTTP caching but
  do not prove every browser or OS copy is absent.
- Use the candidate's single-writer directories, source policy and authority,
  hourly in-process purge and startup cleanup. Record the physical-deletion
  deadline and operator procedure before activation, including stopped bridges,
  failures, termination, and host-off periods. No process can delete data while
  the machine is off. Follow the [candidate runbook](tmdb-live-cache-candidate.md)
  for the scoped inventory and stopped-writer purge; do not claim exact
  seven-day physical deletion from hourly or restart cleanup.

## Remaining boundaries before activation

Review the interpretation of the current source terms and third-party content
for this exact use; verify the actual interface attribution, one-film ID scope,
backup/sync boundary and deletion procedure; and record an explicit,
time-bounded policy and independent authority. If those checks cannot support
the proposed decision, leave the cache disabled. Reassess before changing the
purpose, adding users or films beyond this pilot, retaining history, enabling
commercial or model-based use, or redistributing data. The broader provider
selection and empirical product gates remain separate.
