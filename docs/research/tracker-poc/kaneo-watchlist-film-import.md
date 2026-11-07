# Kaneo watchlist-film import evidence

The two current Movary watchlist entries already have neutral YouTrack issues,
but do not yet have Kaneo tasks. The preview-first `kaneo_watchlist_films.py`
tool is prepared to create those tasks without changing Movary, watchlist
membership, preferences, existing tasks, or contacting a metadata provider.
The supplied TMDb identities have not been independently verified.

The tool checks the API-key owner against the current project and observed
watchlist, inventories all task pages including archived tasks, and stops on
identity or title conflicts. It rechecks the reviewed private preview before
each create, verifies the created fields, and stops on an uncertain response.
Run it with a single writer: Kaneo does not enforce uniqueness of the external
ID. A separately issued Kaneo API key is required; `store_kaneo_key.py`
validates read access and stores it in the ignored owner-only project cache.
The helper does not test write access.

Synthetic checks cover conflicts, pagination, idempotence and uncertain writes.
An isolated Kaneo 2.49.0 server test using a fresh fictional API key exercised
neutral creation, archived-task inventory, repeat import and preservation of an
existing synopsis. No real film has been imported by this tool yet. The actual
user-facing browser result is still unverified.
