# Provider-neutral offer contracts — C4 offline slice

`availability.opportunity.Opportunity` identifies the work, service, offer kind,
country, exact plan, add-on, quality and cut. Its identity excludes the reporting
source. `Assertion` separately preserves source URL/check time, price/currency,
personal entitlement, reviewed/unresolved/cut-uncertain work status and any
provider-asserted addition/expiry. Unknown values remain nullable.

`access_check.opportunities` groups source assertions without flattening their
price/entitlement disagreements. `first_seen_by_us` is the earliest supplied
observation time, never a provider arrival assertion. Catalog discovery requires
no consumer login; `purchase_ready` separately requires reviewed identity,
confirmed access, known applicable plan/add-on and explicit price/currency.
This is a qualification check, not independent proof of a provider's claim.

`Fetch` scopes observations to source, work and country, with an explicit plan
scope and work-review assertion. Generic subscription presence cannot fill a
known plan scope. `reconcile.changes` only compares complete, reviewed, matching
source/work/country/plan scopes in time order. Unknown, partial, unreviewed or
unknown-plan comparisons produce no events. `source_absent` means absence from
that one qualified source snapshot; it does not assert absence from another
source or account. Repeating an unchanged complete snapshot yields no event.
Callers must retain their last successful complete snapshot on failed/partial
requests rather than replacing it. These pure functions write no cache or event
ledger and send no alerts.

All checks use synthetic observations. No new feed adapter, provider selection,
polling cadence, live acquisition, retention grant or production history is
introduced. Existing tentative TMDB normalization is unchanged. Stable service
and plan IDs still require reviewed provider mapping; equal labels alone are
not identity evidence. C1/C8 persistence, policy expiry and recovery integration
remain production prerequisites. Rights must be resolved for the exact intended
use before any production history is stored, including TMDB's six-month ceiling
and termination purge and native-provider attribution/AI-use restrictions.

Issue #22 remains open until genuine three-date B4 #14 evidence and reviewed B8
#18 select permitted production integration, with quotas, retained-copy purge,
account-plan validation and real recovery acceptance. This slice neither waives
those gates nor changes the already scheduled B4 collection jobs.
