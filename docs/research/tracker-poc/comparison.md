# Kaneo and YouTrack: evidence in progress

This is a working comparison, not a product decision. The experiment runs on a
local Mac with Kaneo 2.49.0 and YouTrack Server 2026.2.19728; no Hermes
deployment or Cloud instance has been tested. The detailed evidence and
reproduction instructions are in [README.md](README.md).

These scores are provisional: the latest YouTrack interface has passed a
fictional browser walkthrough, but the real-film browser path, upgrades and
complete recovery still need verification. The user
prioritized the single-user workflow over additional multi-account tests. An
attractive API or a passing mock is not evidence that the complete workflow
works.

| Criterion | Weight | Kaneo | YouTrack |
| --- | ---: | ---: | ---: |
| Freedom to create a substantially different UI | 30% | 4 | 3 |
| Data-model flexibility | 15% | 3 | 4 |
| APIs and external agent integration | 15% | 3 | 4 |
| Searching, sorting, and filtering | 10% | 2 | 3 |
| Lifecycle and automation | 10% | 2 | 5 |
| Deployment and operating complexity | 10% | 3 | 3 |
| Upgradeability and long-term maintenance | 10% | 2 | 3 |
| **Weighted total, out of 5** | **100%** | **3.00** | **3.50** |

These are engineering judgments from this limited POC, not measured future
costs. Kaneo scores higher on interface freedom because a standalone UI works
with its public source and an upstream fork was unnecessary; its observed
search limit, separate preference store and version-specific API behavior lower
the other scores. YouTrack scores higher for typed fields, native queries and
tested workflow rules, while its iframe and surrounding interface constrain the
experience and its app-owned data requires a recovery plan. Both operating
scores reflect extra local services and untested recovery; the substantially
larger YouTrack memory sample is not a production sizing comparison.

**Provisional recommendation: continue with YouTrack** if the remaining
browser and operational checks confirm the embedded page is usable. It has demonstrated
more of the requested persistence, query and automation capabilities without a
source fork, which may reduce ongoing backend work. Kaneo remains the stronger
candidate if a tracker-free interface is decisive or YouTrack's app/data
lifecycle proves burdensome. Do not treat this as a final selection until the
unfinished browser, recovery and upgrade checks have been resolved.

| Criterion and weight | Kaneo evidence | YouTrack evidence | Remaining evidence |
| --- | --- | --- | --- |
| Custom UI freedom, 30% | A separate React UI uses the logged-in Kaneo session and local APIs. An isolated Brave session opened a fictional film and persisted a synopsis, lifecycle and interest score through reload. Source is available for a fork, but this experiment did not require one. | The latest main-menu iframe rendered 763 active fictional cards. A Brave walkthrough created and edited a fictional film, persisted interest and watched status, opened a direct link and exercised archive filtering. The iframe omits `allow-forms`, requiring direct button handlers; the YouTrack sidebar remains visible. | Verify live metadata and posters in YouTrack and remaining navigation. Test standalone YouTrack authentication in a browser. |
| Data model, 15% | Numeric and multiselect task fields were read and written. Per-user data uses a small separate SQLite bridge and is not native task-field data. Current task-wide provenance is neutral, but the original import named the personal source and historical storage exposure is unassessed. | Typed issue fields and a separate lifecycle field were exercised; shared provenance was sanitized. A fictional preference and watched snapshot passed live single-user tests, and the real watched snapshot was read back. Deleting the app also deletes its extension properties. | Assess old Kaneo provenance in history/backups, and verify deletion and recovery behavior and practical per-user size limits. |
| API and agents, 15% | The running OpenAPI document and REST endpoints were inspected; a synthetic external worker repeats without duplicate creation in sequential tests. | A token-authenticated external worker created and updated fictional issues. A local import contains 130 film records with supplied IDs, checked import mappings and sanitized field provenance; the film identities are not independently verified. | Test narrow credentials and signed-in permissions. Measure upgrade stability and repeat behavior with the complete app. |
| Search and sorting, 10% | Board pagination returned 1,000 synthetic tasks. The observed broad native search was capped at 50; the UI joins preferences and sorts them numerically. | A typed global critic-score sort returned 1,000 synthetic issues through paginated REST. Per-user interest sorting is performed by the proposed UI, not that native query. | Exercise identical provider, interest, genre and freshness filters in both browsers, including unknown data and 1,000-film rendering. |
| Lifecycle and automation, 10% | Fictional tasks moved through columns; synthetic archive/restore and history were checked via API. External orchestration is still needed for the demonstrated enrichment. | Typed lifecycle updates and history were checked through REST. The installed on-change rule rejected one transition and allowed another on its guarded fictional issue; the scheduled rule wrote its marker. | Verify workflow history and the user-facing lifecycle experience in both browsers. |
| Deployment and operations, 10% | Docker and PostgreSQL run locally with separate bridges. A fictional database dump restored a record, field and comment into a separate Kaneo instance and survived its restart. Four point-in-time samples showed about 245 MiB combined container memory, excluding bridges and Docker overhead. | The local Docker server uses its integrated database, a film-browser app and a separate metadata-bridge app plus service. The same brief sample showed about 2.07 GiB container memory, excluding the bridge and other overhead. Cloud is documented but untested. | Test YouTrack recovery and Kaneo attachments/preferences; measure controlled startup, secret rotation and Hermes. The sampled workloads and data are not identical. |
| Upgrades and maintenance, 10% | The separate UI avoids an upstream source fork but depends on version-specific API behavior and separate bridge maintenance. | Official app and host APIs avoid modifying private UI internals, but app updates, iframe constraints and app-owned data lifecycle need verification. | Perform a pinned-version upgrade rehearsal and record actual merge and migration work. |

## Shared data and enrichment

The local private input contains 103 discovery candidates and 27
Movary-supplied watched IDs. Those watched-only identifiers have not been
independently verified. Both trackers hold canonical records. Kaneo has a
read-only, user-gated Movary sidecar, and the 27-film watched snapshot was
imported into the local YouTrack administrator's app-owned property after a
fictional single-user and anonymous-denial check. A later guarded app update
migrated that snapshot to mixed v2, preserving all 27 issue/event histories
with 16 inferred ID bindings and 11 unbound. A later v3 refresh added 27 current
entries from a newer Movary observation and retained the 11 unbound histories
separately with their original observation time. The old and new source events
matched, but the bindings and supplied IDs do not independently verify film
identity. The other project's watched projection and visible preferences,
settings, usages and attachments were unchanged in the checked observations.
Owner-only full-property exports were saved before and after the v3 refresh;
the older v1 project projections were visibility-filtered, not full backups.
A full-property restore passed in an isolated fictional app; real restoration
and full server recovery remain unverified. The Kaneo sidecar was subsequently
updated to the newer observation time after its 27 watched IDs and event arrays
were verified identical; the sidecar's other bytes were unchanged. Neither
import writes to Movary or changes a watchlist.

An aggregate read of the 130 YouTrack issues on 2026-11-06 found no nonempty
issue description, stored release year, stored genre, critic score or critic
summary. The source-listed director field was populated for 54 issues and the
direct-review-links field for 50. A later targeted import added one previously
researched critic-review link to an untouched YouTrack issue, bringing its
review-field coverage to 51 films; Kaneo had not received that additional
link at the time of the import. The source match is not an independently
verified film identity. See [direct-review links](direct-review-links.md) for
the import and its limits. The private input likewise has no synopsis,
canonical release year or genre. These counts describe the issue fields, not
the separate TMDB cache. They expose a material gap against the requested
persistent canonical film model: the POC can display cached synopsis, year and
genre while available, but has not demonstrated a rights-compatible way to
retain those TMDB-derived details indefinitely. This is not evidence that the
tracker cannot store those field types.

Both discovery grids can display a stored source-listed year when its source
evidence has valid links and matches the film's current supplied TMDB ID. Kaneo
uses it when neither a stored release year nor a matched live year is available;
YouTrack keeps its stored release year separate and uses the live year if no
usable stored or source year is present. The label identifies an editable
source field and asks the user to verify identity and edits: the saved evidence
does not record the original title and cannot prove the current title or field
value is unchanged. Changed IDs or invalid source evidence withhold the source
year. The existing private input contains source-listed years with available
source evidence for 87 of 130 films. A subsequent read-only YouTrack check
matched all 130 film IDs and source-year values against the input and found
that 87 stored years passed the exact UI helper's identity and evidence guard.
This is not a verified release-year count or real-film browser check. Fictional
tests cover missing/malformed evidence, changed IDs and year
precedence. Both updated UI bundles matched their reviewed builds after
deployment; the complete YouTrack watched property and checked app state were
unchanged. No tracker metadata was rewritten.

The opt-in TMDB reader can retain normalized metadata in a separate local
seven-day cache without writing the response to tracker history. Both trackers
have cached all 130 approved records. A cache-only comparison found identical
metadata and availability statuses for all 130; the 109 comparable complete
provider sets matched, and 21 observations were unknown in both. Each bridge
was restarted, after which all 130 cache entries remained readable. This does not
establish identity accuracy, individual streaming entitlement, or rights for
indefinite storage. An isolated Kaneo browser displayed the real 130-card
grid, loaded all cache records and retained a selected film’s cached detail
across reload and back navigation; its poster bytes were substituted locally. A fresh isolated
YouTrack browser reached sign-in, but the API token did not create a browser
session, so the real-film YouTrack browser path remains outstanding. Fictional
mounted browsers verified cache rehydration and transient poster rendering.
An aggregate live details check returned valid records for all 130 input IDs;
110 titles exactly matched after normalization and 20 did not. Alternate titles
can explain differences, so those results do not settle film identity. A later
non-retaining check found nine additional original-title matches under its
Unicode/casefold/whitespace comparison. The UI now accepts an exact normalized
current or original title as a display guard; this comparison uses slightly
different normalization and neither establishes identity. The earlier
identity checks retained no provider response bodies. A later local comparison
against the imported manifest found 11 titles withheld by the UI guard. Five
of those differed only under a broader accent/punctuation comparison; ten had
matching source years and six matching source directors. Those counts overlap,
source years can represent a different date, and none proves a match. The
comparison used the imported manifest rather than any subsequently edited
tracker title. The new detail panel shows the available source and returned
facts for manual review while continuing to withhold mismatched artwork and
offers. Conversely, an exact title match can still identify the wrong film;
the current guard does not automatically resolve conflicting year or director.
An offline comparison of the nine validated private review batches against the
unexpired local YouTrack cache found existing review evidence for six of those
11 withheld source-manifest films. Five of the six had a reviewed source-page
title matching the cached TMDB title or original title; their source-listed
years also matched, and four had a matching source director. These observations
do not establish an independent film identity or independent source lineage.
Both deployed identity-review panels can show the matching existing review
title and link as an unverified lead, after checking the supplied ID and saved
title. The links require a user action to open; artwork and provider offers
remain withheld. Fictional rendering and identity-guard checks passed, and a
local in-memory rendering against the validated manifests and cache produced
five such panels. This was not a current tracker-field or real-film browser
rendering check. The deployed bundles matched their reviewed builds and the
checked watched property and app settings were unchanged.
Both film-detail pages can now also read limited facts from the existing
reviewed catalog without copying it into either tracker or making a TMDB API
request. The shared credits component requests TMDB's generic logo without a
film referrer when catalog facts are displayed.
A collection-wide local check of all 130 approved records found that both
tracker endpoints returned facts for the same 95 films, with no disagreements.
Fictional browser checks verified the display and reload with mocked endpoint
responses. Catalog expiry is enforced; synopsis, poster references and provider
observations instead use the separate seven-day cache. See [the POC README](README.md).
In later sequential non-retaining checks, both local backends read all 130
authorized IDs: each returned 130 poster paths and 109 complete US provider
responses; 21 provider results were unknown. An isolated Kaneo browser check
confirmed a matching film's poster loaded and provider information appeared;
another returned title differed, so the interface withheld that artwork and
availability. The YouTrack widget can request live data on demand; the real-film browser
integration remains unverified. A trusted-keyboard browser check reached the actual
fictional fixture handler and rendered its title and synopsis; the provider
and poster were locally mocked. The fixture's HTTP 429 also produced a visible
rate-limit message and prevented another request. The optional MDBList endpoint returned HTTP 403, so no live MDBList enrichment
is claimed. Source-list links remain labeled by their actual source and lineage;
they are not automatically independent critic reviews.

The initial build effort has not been tracked in comparable person-hours. The
existing measurements are local API timings and cannot predict production
capacity or ongoing maintenance. The provisional scores above should be revisited
after the same end-to-end workload on both candidates and the outstanding
recovery and upgrade checks.

For a safe future recovery rehearsal, create separate fictional-only instances
with their own bind directories, ports and credentials. Changing the Compose
project name alone does not isolate the existing POC's configured mounts and
ports. A Kaneo rehearsal should restore a PostgreSQL dump into a new empty test
database and separately check its preference store and any attachments. A
YouTrack rehearsal should restore a fictional backup into a new instance and
check the app and its extension properties, as well as issues and attachments.
The isolated [Kaneo fictional database rehearsal](kaneo-recovery-rehearsal.md)
passed for its small fixture; a separate offline SQLite preference backup and
restore also passed for one fictional row. A fictional Waitress service check
subsequently read the restored preference and rejected an old preview across
restart; authentication was mocked. Kaneo's local POC has no object-storage
configuration, and an upload request against a separate fictional instance
returned HTTP 503. A later separate fictional fixture configured Garage as an
S3-compatible store: database-only restore returned HTTP 404 for the original
image even while a control upload/read succeeded; restoring the stopped store
as well recovered the exact image bytes across app and store restart. This does
not configure attachment storage in the live POC or establish production
recovery. YouTrack recovery and live preference-service recovery remain
untested. See the [fictional attachment rehearsal](kaneo-recovery-rehearsal.md#attachment-backup-and-restore-with-fictional-object-storage), official [PostgreSQL 16 dump
documentation](https://www.postgresql.org/docs/16/app-pgdump.html) and
[YouTrack Docker restore guide](https://www.jetbrains.com/help/youtrack/server/restore-docker-image-installation.html).
The current Compose file does not establish automatic startup after a host
reboot; Hermes has not been tested.

On 2026-11-05, YouTrack's [documented manual backup API](https://www.jetbrains.com/help/youtrack/devportal/api-usecase-backup.html)
created one database-and-attachments archive in the existing project-local
backup directory. YouTrack reported success, the archive listing passed an
integrity check, and YouTrack could read it after its permissions were changed
to owner-only. This is a local copy on the same machine, not an off-device
backup or a restore test. Automatic backups remain disabled; extension-property
recovery is unverified. The archive contains private project data and must stay
out of Git. Future backups need their permissions checked as well.

For a narrower CPU-only check, the two client filtering functions were run
separately in warmed Node processes against the same 1,000 fictional films.
The Netflix-plus-interest filter and numeric sort had medians of 0.643 ms for
Kaneo and 0.799 ms for the YouTrack candidate before installation. These are separate
runs, not a controlled browser comparison, and exclude requests, rendering and
images. See the [Kaneo](kaneo-filter-benchmark.md) and
[YouTrack](youtrack-filter-benchmark.md) methods and full samples.

In one uncontrolled local run, 130 sequential authenticated cache-only GETs
using existing approved tracker mappings took 7.38 seconds for Kaneo (p50
56.4 ms; p95 60.2 ms) and 10.93 seconds for YouTrack (p50 82.7 ms; p95
92.7 ms). Mapping construction, provider calls, browser rendering and images
were excluded. These samples are not production benchmarks.

Separately, one in-process run against 130 fictional fresh records took 2.577
seconds for the current cache reader, which scans the cache for purge work on
each read. A lower-bound loop that read the policy and individual record took
0.090 seconds but omitted payload conversion and full-directory purge checks.
This difference identifies repeated scanning as a candidate for investigation;
it is not a measured result of an implemented optimization. The current scan
continues to detect policy changes and unresolved corrupt records on each read.

In separate, uncontrolled browser walkthroughs, Kaneo displayed approximately
1,003 fictional cards in roughly 0.9–1.9 seconds. The embedded YouTrack page
displayed 763 active cards from its roughly 1,000-issue project at about 11
seconds, and a later direct-link revisit took about 20 seconds. The workloads,
browser sessions and measurements were not controlled; they show where to
investigate, not comparative production capacity.

A follow-up fictional YouTrack profile saw the first cards at about 24.5
seconds on a cold browser run, with the iframe becoming ready around 23
seconds; issue pages themselves spanned roughly 1.2 seconds. A later navigation
in the same process took about 2 seconds. Asking for 500 issues per page reduced
request count but did not improve the observed warm samples, so the UI retains
the 100-row page size. The test's request interception disables the browser HTTP
cache, which can inflate startup time; this is not a normal Brave or Hermes
benchmark. See [Playwright's routing documentation](https://playwright.dev/docs/api/class-browsercontext#browser-context-route).
