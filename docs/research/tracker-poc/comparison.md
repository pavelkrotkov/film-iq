# Kaneo and YouTrack: evidence in progress

This is a working comparison, not a product decision. The experiment runs on a
local Mac with Kaneo 2.49.0 and YouTrack Server 2026.2.19728; no Hermes
deployment or Cloud instance has been tested. The detailed evidence and
reproduction instructions are in [README.md](README.md).

The requested scores and weighted totals are pending browser-level and
multiuser tests. An attractive API or a passing mock is not evidence that the
complete workflow works.

| Criterion and weight | Kaneo evidence | YouTrack evidence | Remaining evidence |
| --- | --- | --- | --- |
| Custom UI freedom, 30% | A separate React UI uses the logged-in Kaneo session and local APIs. Source is available for a fork, but this experiment did not require one. | A first main-menu iframe rendered a fictional issue and persisted a synopsis edit across reload. The richer app is installed and showed 130 text-labeled cards with placeholder artwork; a later navigation fix still needs browser verification. A temporary exact-origin CORS setting passed a standalone API preflight and was restored. | Click through equivalent screens, deep links, reload and navigation; measure visible tracker chrome and sandbox limitations. Test standalone authentication and user permissions in a browser. |
| Data model, 15% | Numeric and multiselect task fields were read and written. Per-user data uses a small separate SQLite bridge and is not native task-field data. Current task-wide provenance is neutral, but the original import named the personal source and historical storage exposure is unassessed. | Typed issue fields and a separate lifecycle field were exercised; shared provenance was sanitized. A fictional preference and watched snapshot passed live single-user tests, and the real watched snapshot was read back. Deleting the app also deletes its extension properties. | Assess old Kaneo provenance in history/backups, and verify deletion and recovery behavior and practical per-user size limits. |
| API and agents, 15% | The running OpenAPI document and REST endpoints were inspected; a synthetic external worker repeats without duplicate creation in sequential tests. | A token-authenticated external worker created and updated fictional issues. A local import contains 130 canonical records, with validated source identity and sanitized field provenance. | Test narrow credentials and signed-in permissions. Measure upgrade stability and repeat behavior with the complete app. |
| Search and sorting, 10% | Board pagination returned 1,000 synthetic tasks. The observed broad native search was capped at 50; the UI joins preferences and sorts them numerically. | A typed global critic-score sort returned 1,000 synthetic issues through paginated REST. Per-user interest sorting is performed by the proposed UI, not that native query. | Exercise identical provider, interest, genre and freshness filters in both browsers, including unknown data and 1,000-film rendering. |
| Lifecycle and automation, 10% | Fictional tasks moved through columns; synthetic archive/restore and history were checked via API. External orchestration is still needed for the demonstrated enrichment. | Typed lifecycle updates and history were checked through REST. The installed on-change rule rejected one transition and allowed another on its guarded fictional issue; the scheduled rule wrote its marker. | Verify workflow history and the user-facing lifecycle experience in both browsers. |
| Deployment and operations, 10% | Docker and PostgreSQL run locally along with the separate UI and preference and optional enrichment bridges. Four point-in-time samples showed about 245 MiB combined container memory, excluding those bridges and Docker overhead. | The local Docker server uses its integrated database and one app package; the external enrichment path remains separate. The same brief sample showed about 2.07 GiB container memory. Cloud is documented but untested. | Measure controlled startup and load, recovery and backup, secret rotation, and the cost of a Hermes deployment. The sampled workloads and data are not identical. |
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
responses; 21 provider results were unknown. The new YouTrack widget can request
live data on demand, but its browser integration and image caching remain
unverified. The optional MDBList endpoint returned HTTP 403, so no live MDBList enrichment
is claimed. Source-list links remain labeled by their actual source and lineage;
they are not automatically independent critic reviews.

The initial build effort has not been tracked in comparable person-hours. The
existing measurements are local API timings and cannot predict production
capacity or ongoing maintenance. A recommendation should follow the same
end-to-end workload on both candidates, with incomplete requirements identified
and the seven scores justified against that evidence.

For a narrower CPU-only check, the two client filtering functions were run
separately in warmed Node processes against the same 1,000 fictional films.
The Netflix-plus-interest filter and numeric sort had medians of 0.643 ms for
Kaneo and 0.799 ms for the YouTrack candidate before installation. These are separate
runs, not a controlled browser comparison, and exclude requests, rendering and
images. See the [Kaneo](kaneo-filter-benchmark.md) and
[YouTrack](youtrack-filter-benchmark.md) methods and full samples.
