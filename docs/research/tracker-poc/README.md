# Kaneo and YouTrack comparison — work in progress

This is an isolated evaluation, not a change to FilmIQ's accepted architecture.
Movary remains the source of truth for real watched history, ratings, and the
intentional watchlist. Use synthetic films and users for these experiments.

## Evidence collected so far

* Kaneo source inspected: release `v2.49.0`, commit
  `e0ebc61748654f4e33e713dcb441be726ec1cfc4`. Its custom-field schema
  supports text, number, date, dropdown, boolean, and multiselect. Values are
  stored as strings; multiselect values are JSON arrays. A value is keyed by
  task and field, not by task, field, and user. This is source inspection, not
  a running API test. See [schema](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/src/custom-field/schema.ts),
  [validation](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/src/custom-field/controllers/set-custom-field-value.ts),
  and [migration](https://github.com/usekaneo/kaneo/blob/v2.49.0/apps/api/drizzle/0045_fantastic_princess_powerful.sql).
* Kaneo's source configures credentialed CORS with explicitly configured
  origins in production, and publishes an OpenAPI endpoint. These observations
  do not establish that a separate frontend works or that every endpoint is a
  stable public contract. Verify against the running instance.
* YouTrack documents `MAIN_MENU_ITEM`, `PROJECT_TAB` and issue-page widget
  extension points. `showHeader: false` hides the page header for a main-menu
  widget, but does not prove the rest of the surrounding interface can be
  hidden. [Extension points](https://www.jetbrains.com/help/youtrack/devportal/apps-reference-extension-points.html).
* YouTrack extension properties can attach app-owned data to user entities, but
  deleting the app deletes its extension-property values. Extension-property
  search does not replace native range filtering or sorting in issue lists.
  A per-user film map is therefore a candidate to test, not a demonstrated
  storage or authorization solution. [Properties](https://www.jetbrains.com/help/youtrack/devportal/apps-extension-properties.html),
  [FAQ](https://www.jetbrains.com/help/youtrack/devportal/apps-faq.html).
* The [current YouTrack pricing page](https://www.jetbrains.com/youtrack/buy/)
  describes free plans for up to ten users for Cloud and Server. Cloud includes
  30 GB; check current terms and other limitations before deployment.

## Outstanding

Neither POC has been run or implemented yet. No screen, performance, security,
upgradeability, automation, availability, or persistence acceptance test has
passed. Do not score or recommend either product based on the preliminary
observations above. Record the tested image versions, results, failures, and
remaining gaps here as the evaluation proceeds.
