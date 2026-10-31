# Viewing-plan report

`film-iq report --database evidence.db --inputs private-inputs.json --snapshot private-snapshot.json`
reads current accepted evidence and the complete Movary snapshot. Its sibling
`.status` file must identify the same successful refresh. Watched films are
excluded using that snapshot, overriding old input flags; both personal scores
are retained separately and never blended into critical recognition utility.
Omitting `--snapshot` retains the older caller-supplied watched-state mode.
No command here changes Movary, subscribes or purchases.

The existing inputs contain `catalog` keyed by Film-IQ work ID (title, minutes,
watched), `checked_at`, raw TMDB `offers`, current numeric service IDs, viewing
`dates`, `max_minutes`, `max_films`, `budget_cents`, `service_prices_cents` and
`rental_prices_cents`. Prices are integer USD cents including tax; null service
prices remain unknown and exclude that purchase. `utility_power` defaults to 1;
run with 2 to compare a stronger preference for fewer highly recognized films.
This declared sensitivity is not a learned personal recommendation model.

The JSON and Markdown include separate **verified** and **exploratory** plan
comparisons. Both compare no purchase, rentals, one new service and that service
plus rentals. Existing subscriptions are sunk costs. Legacy TMDB offers remain
unconfirmed because they do not prove price, tier or account entitlement.

For a reviewed provider-neutral snapshot, supply `assertions` instead of using
legacy offers for planning. Each item is an `Assertion` object with a nested
`opportunity` and an additional positive integer `provider_id`. That ID must
identify exactly one service/plan/add-on combination throughout this input;
separate tiers need separate IDs. Its original source, check time, URL, plan,
add-on, work/cut status and price assertions remain in JSON. ISO timestamps must
include offsets. Also supply explicit `assessed_at` and `offer_max_age_hours`;
these are declared assessment/freshness assumptions, not a polling schedule.

Only reviewed US work with a fresh, currently valid assertion enters planning.
Non-USD prices cannot enter this USD planner. Confirmation additionally requires
C4's purchasing qualification: explicit price/currency, applicable entitlement,
known tier/add-on where relevant, and acceptable time window. A new subscription
fee must match its exact plan's USD assertion; unknown fees are not zero.
Date-only viewing slots conservatively exclude the whole asserted expiry day,
because the report cannot prove a viewing ends before an intraday deadline.
Unknown expiry stays unknown. Sources and entitlement still require independent
verification: supplying this JSON does not clear provider rights or Gate B.
