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

Free/ad-supported access with a known nonzero price is contradictory and is
rejected before planner filtering, for both direct `Access` callers and source
assertions. Unknown prices remain unknown rather than being rewritten to zero.
Viewing dates must be on or after the calendar day of caller `assessed_at`, or
legacy `checked_at`, in that timestamp's declared timezone. Same-day slots are
allowed because slots have no time of day; this does not prove that a viewing
starts after an intraday assessment/arrival. Historical assessments remain valid
for backtests. Assertions with a future provider-supplied arrival are already
ineligible at assessment; no future-access guarantee or new solver is added.

Each Markdown choice shows its known USD price or explicit unknown, with rentals
labelled one-off and recurring service/add-on fees labelled assumptions/sunk
costs rather than additional per-film charges. Its conservative last full viewing
day is separate from the selected source's actual asserted expiry timestamp;
unknown dates stay unknown. The selected assertion's original citation and
entitlement are preserved. These are caller-supplied facts/assumptions, not an
independent verification of provider accuracy or tax treatment.

The conservative expiry day uses the assessment timestamp's timezone, matching
viewing-slot dates; the original provider expiry retains its supplied offset.
For legacy subscription access without a source price, a supplied service fee
is separately preserved in `service_price_assumptions` and labelled caller-
declared in the choice text. A known selected assertion price takes precedence.
This neither invents a billing interval nor adds a second per-film fee; absent
existing-service fees remain unknown and sunk.
