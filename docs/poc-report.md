# Dry-run POC report

Run `uv run film-iq report --database path/to/evidence.db --inputs path/to/report-inputs.json`.
Markdown is the default; add `--format json` for machine-readable output. The
database is opened read-only. The command does not migrate, accept evidence,
change identities, fetch provider data or write to Movary. It emits JSON with
source citations, rank and completeness context, excluded derivative evidence,
US offer status and observation time, feasible plans, costs, assumptions and
watchlist previews for each plan's selected films. The explicit internal-film to
TMDB crosswalk connects recommendations to their evidence without relying on array order.

Inputs are authorized local snapshots, not proof of real-world availability or
entitlement. Catalog keys are internal film IDs; provider payload keys are TMDB
IDs. The stored crosswalk is required. For example (synthetic identifiers):

```json
{
  "catalog": {"42": {"title": "Fixture film", "minutes": 90, "watched": false}},
  "checked_at": "2026-10-29T12:00:00+00:00",
  "offers": {"1": {"id": 1, "results": {"US": {
    "link": "https://example.test/watch",
    "free": [{"provider_id": 7, "provider_name": "Fixture provider"}]
  }}}},
  "current_services": [],
  "dates": ["2026-11-01"],
  "max_minutes": 90,
  "max_films": 1,
  "budget_cents": 500,
  "service_prices_cents": {},
  "rental_prices_cents": {}
}
```

Rental price keys are `TMDB_ID:PROVIDER_ID`, with values in integer USD cents.
Unknown rental prices are excluded from rental choices; TMDB supplies no prices.
Service prices must include applicable taxes. Current service IDs are supplied
by the caller, but plan-specific entitlement remains unconfirmed. Missing or
failed provider responses remain unknown. The report displays snapshot times;
it does not claim those snapshots are still current. Titles, runtimes and watched
status are caller-supplied and must be reconciled with the authoritative sources.

Only current accepted matches and explicitly verified independent original
evidence contribute. Derivative evidence remains in explanations without adding
votes. Unverified evidence cannot be made eligible through this input file.
The count-based planner utility is provisional and uncalibrated; its version and
limitations appear in each plan's assumptions. A synthetic report does not close
Gate A. An eventual live Movary action needs a separately approved selected
preview through the approved-write boundary.
