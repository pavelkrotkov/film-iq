# Movary watchlist component verification

On November 6, 2026, the shared `MovaryWatchlist` source component was bundled
and rendered in memory with React's server renderer. The inputs were the
current user-scoped YouTrack watchlist endpoint and the 130 issues visible to
the local administrator in `FILMREAL`. The component produced two rows: zero
matched, two unmatched, and zero ambiguous. Both rows rendered a **Prepare Add
film** button. Film details were not printed or stored by this check.

The same component was also rendered with the Kaneo user's local watchlist
sidecar and that same YouTrack issue list. It produced the same aggregate
counts. This was a comparison against the YouTrack manifest, not a check of
live Kaneo issue data.

The check used the reviewed component source, not a browser execution of the
deployed bundles. It does not verify authenticated browser rendering, button
interaction, navigation, individual film identity, other users' access, or
records invisible to the administrator. An unmatched entry means it did not
match a visible input record; it is not a claim about any other project or
source. Earlier deployment checks verified served or installed bundle bytes
separately. No provider, browser, Movary, or write requests were made during
this render check.
