# Kaneo and YouTrack: evidence in progress

This is a working comparison, not a product decision. The experiment runs on a
local Mac with Kaneo 2.49.0 and YouTrack Server 2026.2.19728; no Hermes
deployment or Cloud instance has been tested. The detailed evidence and
reproduction instructions are in [README.md](README.md).

These scores are provisional: the latest YouTrack interface has passed a
fictional browser walkthrough, but live metadata there, upgrades and complete
recovery still need verification. The user
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

**Provisional recommendation: continue with YouTrack** if the remaining live
metadata and operational checks confirm the embedded page is usable. It has demonstrated
more of the requested persistence, query and automation capabilities without a
source fork, which may reduce ongoing backend work. Kaneo remains the stronger
candidate if a tracker-free interface is decisive or YouTrack's app/data
lifecycle proves burdensome. Do not treat this as a final selection until the
unfinished browser, recovery and upgrade checks have been resolved.

| Criterion and weight | Kaneo evidence | YouTrack evidence | Remaining evidence |
| --- | --- | --- | --- |
| Custom UI freedom, 30% | A separate React UI uses the logged-in Kaneo session and local APIs. An isolated Brave session opened a fictional film and persisted a synopsis, lifecycle and interest score through reload. Source is available for a fork, but this experiment did not require one. | The latest main-menu iframe rendered 763 active fictional cards. A Brave walkthrough created and edited a fictional film, persisted interest and watched status, opened a direct link and exercised archive filtering. The iframe omits `allow-forms`, requiring direct button handlers; the YouTrack sidebar remains visible. | Verify live metadata and posters in YouTrack and remaining navigation. Test standalone YouTrack authentication in a browser. |
| Data model, 15% | Numeric and multiselect task fields were read and written. Per-user data uses a small separate SQLite bridge and is not native task-field data. Current task-wide provenance is neutral, but the original import named the personal source and historical storage exposure is unassessed. | Typed issue fields and a separate lifecycle field were exercised; shared provenance was sanitized. A fictional preference and watched snapshot passed live single-user tests, and the real watched snapshot was read back. Deleting the app also deletes its extension properties. | Assess old Kaneo provenance in history/backups, and verify deletion and recovery behavior and practical per-user size limits. |
| API and agents, 15% | The running OpenAPI document and REST endpoints were inspected; a synthetic external worker repeats without duplicate creation in sequential tests. | A token-authenticated external worker created and updated fictional issues. A local import contains 130 canonical records, with validated source identity and sanitized field provenance. | Test narrow credentials and signed-in permissions. Measure upgrade stability and repeat behavior with the complete app. |
| Search and sorting, 10% | Board pagination returned 1,000 synthetic tasks. The observed broad native search was capped at 50; the UI joins preferences and sorts them numerically. | A typed global critic-score sort returned 1,000 synthetic issues through paginated REST. Per-user interest sorting is performed by the proposed UI, not that native query. | Exercise identical provider, interest, genre and freshness filters in both browsers, including unknown data and 1,000-film rendering. |
| Lifecycle and automation, 10% | Fictional tasks moved through columns; synthetic archive/restore and history were checked via API. External orchestration is still needed for the demonstrated enrichment. | Typed lifecycle updates and history were checked through REST. The installed on-change rule rejected one transition and allowed another on its guarded fictional issue; the scheduled rule wrote its marker. | Verify workflow history and the user-facing lifecycle experience in both browsers. |
| Deployment and operations, 10% | Docker and PostgreSQL run locally with separate bridges. A fictional database dump restored a record, field and comment into a separate Kaneo instance and survived its restart. Four point-in-time samples showed about 245 MiB combined container memory, excluding bridges and Docker overhead. | The local Docker server uses its integrated database and one app package; the external enrichment path remains separate. The same brief sample showed about 2.07 GiB container memory. Cloud is documented but untested. | Test YouTrack recovery and Kaneo attachments/preferences; measure controlled startup, secret rotation and Hermes. The sampled workloads and data are not identical. |
| Upgrades and maintenance, 10% | The separate UI avoids an upstream source fork but depends on version-specific API behavior and separate bridge maintenance. | Official app and host APIs avoid modifying private UI internals, but app updates, iframe constraints and app-owned data lifecycle need verification. | Perform a pinned-version upgrade rehearsal and record actual merge and migration work. |

## Shared data and enrichment

The local private input contains 103 discovery candidates and 27
Movary-supplied watched IDs. Those watched-only identifiers have not been
independently verified. Both trackers hold canonical records. Kaneo has a
read-only, user-gated Movary sidecar, and the 27-film watched snapshot was
imported into the local YouTrack administrator's app-owned property after a
fictional single-user and anonymous-denial check. Readback matched the source;
neither import writes to Movary or changes a watchlist.

The opt-in TMDB reader retrieves metadata into page memory, with no tracker
write of the response body; a public example ID worked for a signed-in
synthetic user after anonymous access was rejected. This does not establish
accuracy, individual streaming entitlement, or rights for indefinite storage.
An aggregate live details check returned valid records for all 130 input IDs;
110 titles exactly matched after normalization and 20 did not. Alternate titles
can explain differences, so those results do not settle film identity. No
provider response bodies were retained, and this is not a completed enrichment.
In later sequential non-retaining checks, both local backends read all 130
authorized IDs: each returned 130 poster paths and 109 complete US provider
responses; 21 provider results were unknown. An isolated Kaneo browser check
confirmed a matching film's poster loaded and provider information appeared;
another returned title differed, so the interface withheld that artwork and
availability. The new YouTrack widget can request live data on demand, but its browser integration and image caching remain
unverified for real films. A trusted-keyboard browser check reached the actual
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
restore also passed for one fictional row. YouTrack recovery, Kaneo attachments
and live preference-service recovery remain untested. See the official [PostgreSQL 16 dump
documentation](https://www.postgresql.org/docs/16/app-pgdump.html) and
[YouTrack Docker restore guide](https://www.jetbrains.com/help/youtrack/server/restore-docker-image-installation.html).
The current Compose file does not establish automatic startup after a host
reboot; Hermes has not been tested.

For a narrower CPU-only check, the two client filtering functions were run
separately in warmed Node processes against the same 1,000 fictional films.
The Netflix-plus-interest filter and numeric sort had medians of 0.643 ms for
Kaneo and 0.799 ms for the YouTrack candidate before installation. These are separate
runs, not a controlled browser comparison, and exclude requests, rendering and
images. See the [Kaneo](kaneo-filter-benchmark.md) and
[YouTrack](youtrack-filter-benchmark.md) methods and full samples.

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
