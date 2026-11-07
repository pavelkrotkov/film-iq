# YouTrack new-film drafts and project changes

Changing YouTrack projects with an unsaved new-film title or supplied TMDB ID
now requires a discard decision. The project picker and external app-location
changes retain those fields while the decision is pending. Continuing after
confirmation clears them before changing project; remaining in the same
project retains them. This prevents a draft intended for one project from
being silently carried into another project's add-film action.

Fictional actual-handler and route checks cover title-only and ID-only drafts,
the picker, external navigation, keeping the draft, and explicit discard. The
combined UI package built from commit `39a9468` was deployed and read back;
the full watched property and checked app state were unchanged. No real-film
browser walkthrough was performed for this change.

```sh
node docs/research/tracker-poc/ui/youtrack_project_draft_check.mjs
node docs/research/tracker-poc/ui/youtrack_navigation_check.mjs
```
